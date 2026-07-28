#!/usr/bin/env python3
"""Pipeline Kling AI: interior finalizado -> 'antes' -> vídeo de reforma.

Usa o CLI `kling` (repo klingaimcp). Diferente do Agnes, **toda submissão é
cobrada em créditos** da conta Pro/SVIP — por isso nada é enviado sem `--sim`.

    python3 kling/rodar.py --so-imagem --sim
    python3 kling/rodar.py --so-video --sim
    python3 kling/rodar.py --sim

Defaults do Nei (klingai-nei/README.md): resolução 720p em toda geração; a
resposta bruta de cada submit é gravada ANTES de qualquer parse — job pago não
cancela, e ID perdido é crédito perdido.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "agnes"))

import prompts  # noqa: E402  (mesmos prompts, um motor diferente)

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENTRADA = os.path.join(RAIZ, "input", "interior-design.png")
SAIDA = os.path.join(RAIZ, "output")
BRUTO = os.path.join(SAIDA, "kling-respostas")
ANTES = os.path.join(SAIDA, "before-construction.png")
DEPOIS = os.path.join(SAIDA, "completed-interior.png")
VIDEO = os.path.join(SAIDA, "renovation-video.mp4")

# kling-image-o1: "consistência de features, edição precisa" — o que mais
# aproxima de EDITAR o ambiente em vez de reinterpretá-lo.
MODELO_IMG = "kling-image-o1"
# kling-video-v2_5 aceita o par A->B via --tailImage e é o de melhor custo.
MODELO_VIDEO = "kling-video-v2_5"


def submeter(argv: list, rotulo: str, timeout: int) -> dict:
    """Roda o CLI, GRAVA a resposta bruta e só então parseia."""
    os.makedirs(BRUTO, exist_ok=True)
    print(f"[kling] {rotulo}: {' '.join(argv[:6])} …")
    proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    carimbo = time.strftime("%Y%m%d-%H%M%S")
    caminho = os.path.join(BRUTO, f"{rotulo}-{carimbo}.txt")
    with open(caminho, "w", encoding="utf-8") as fh:
        fh.write(f"$ {' '.join(argv)}\n\n--- stdout ---\n{proc.stdout}\n"
                 f"--- stderr ---\n{proc.stderr}\n")
    print(f"[kling] resposta bruta -> {caminho}")
    if proc.returncode != 0:
        raise RuntimeError(f"kling saiu com {proc.returncode}: {proc.stderr[:400]}")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"_texto": proc.stdout}


def extrair_url(resp: dict, extensoes: tuple) -> str:
    """Acha a primeira URL de resultado na resposta (formato varia por modelo)."""
    bruto = json.dumps(resp)
    for m in re.finditer(r"https?://[^\"'\\\s]+", bruto):
        url = m.group(0)
        if url.lower().split("?")[0].endswith(extensoes):
            return url
    raise RuntimeError(
        "não achei URL de resultado na resposta — confira o arquivo bruto em "
        f"{BRUTO} e baixe manualmente (o job foi cobrado, não resubmeta às cegas)"
    )


def baixar(url: str, destino: str) -> str:
    with urllib.request.urlopen(url, timeout=600) as r, open(destino, "wb") as fh:
        fh.write(r.read())
    print(f"[kling] -> {destino} ({os.path.getsize(destino) // 1024} KB)")
    return destino


def preparar_entrada(origem: str) -> str:
    os.makedirs(SAIDA, exist_ok=True)
    shutil.copyfile(origem, DEPOIS)
    print(f"[prep] depois -> {DEPOIS} ({os.path.getsize(DEPOIS) // 1024} KB)")
    return DEPOIS


def prompt_antes() -> str:
    p = prompts.ANTES
    layout = os.environ.get("LAYOUT")
    if layout:
        p = p.replace(
            "It must look like the exact same room",
            f"Room layout, unchanged: {layout}. It must look like the exact same room",
        )
    return p


def etapa_imagem(modelo: str, resolucao: str) -> str:
    resp = submeter(
        ["kling", "image_to_image", "--image", DEPOIS, "--model", modelo,
         "--img_resolution", resolucao, "--aspect_ratio", "16:9",
         "--imageCount", "1", "--poll", "300", prompt_antes()],
        rotulo="imagem", timeout=420,
    )
    return baixar(extrair_url(resp, (".png", ".jpg", ".jpeg", ".webp")), ANTES)


def etapa_video(modelo: str, duracao: str, resolucao: str) -> str:
    resp = submeter(
        ["kling", "image_to_video", "--image", ANTES, "--tailImage", DEPOIS,
         "--model", modelo, "--duration", duracao, "--resolution", resolucao,
         "--imageCount", "1", "--poll", "900", prompts.VIDEO_SEEDANCE],
        rotulo="video", timeout=1200,
    )
    caminho = baixar(extrair_url(resp, (".mp4", ".mov")), VIDEO)
    print(f"[ffprobe] {ffprobe(caminho)}")
    return caminho


def ffprobe(caminho: str) -> str:
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height,nb_frames,r_frame_rate:format=duration",
             "-of", "default=nw=1", caminho],
            capture_output=True, text=True, check=True,
        )
        return " ".join(out.stdout.split())
    except Exception as e:
        return f"(ffprobe indisponível: {e})"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--imagem", default=ENTRADA)
    ap.add_argument("--modelo-img", default=MODELO_IMG,
                    help="kling-image-o1 | kling-image-v3_0_omni | gpt-image2 | gemini-3-pro-image …")
    ap.add_argument("--modelo-video", default=MODELO_VIDEO,
                    help="kling-video-v2_5 | kling-video-v2_6 | kling-video-v3_0_turbo …")
    ap.add_argument("--duracao", default="5", choices=("5", "10"))
    ap.add_argument("--resolucao", default="720p", help="default do Nei: 720p")
    ap.add_argument("--img-resolucao", default="1k")
    ap.add_argument("--so-imagem", action="store_true")
    ap.add_argument("--so-video", action="store_true")
    ap.add_argument("--sim", action="store_true",
                    help="confirma o gasto de créditos — sem isso nada é submetido")
    args = ap.parse_args()

    if not shutil.which("kling"):
        print("erro: CLI `kling` não está no PATH (ver ~/projetos/klingaimcp)")
        return 1

    print(f"[cfg] imagem={args.modelo_img} · vídeo={args.modelo_video} "
          f"· {args.duracao}s {args.resolucao}")
    if not args.sim:
        print("\n⚠️  Toda submissão ao Kling É COBRADA em créditos e não cancela.")
        print("    Reveja os modelos acima e repita com --sim para submeter.")
        return 2

    if not args.so_video:
        if not os.path.exists(args.imagem):
            print(f"erro: imagem não encontrada em {args.imagem}")
            return 1
        preparar_entrada(args.imagem)
        etapa_imagem(args.modelo_img, args.img_resolucao)
        if args.so_imagem:
            print("\nConfira o 'antes' (mesma câmera, mesmas aberturas) antes de "
                  "gastar crédito no vídeo.")
            return 0

    for arquivo in (ANTES, DEPOIS):
        if not os.path.exists(arquivo):
            print(f"erro: o vídeo precisa de {arquivo}")
            return 1
    etapa_video(args.modelo_video, args.duracao, args.resolucao)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
