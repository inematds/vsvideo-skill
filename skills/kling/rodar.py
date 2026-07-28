#!/usr/bin/env python3
"""Sistema KLING — independente. Imagem e vídeo, os dois no Kling AI.

Usa o CLI `kling` (repo klingaimcp). Diferente do Agnes, **toda submissão é
cobrada em créditos** da conta Pro/SVIP — por isso nada é enviado sem `--sim`.

    python3 rodar.py --so-imagem --sim
    python3 rodar.py --so-video --sim
    python3 rodar.py --sim

Esta pasta é autossuficiente: prompts.py e rodar.py vivem aqui.

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

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import prompts  # noqa: E402  (cópia local — esta pasta é autossuficiente)

# raiz do projeto = duas pastas acima (skills/kling/ -> repo/)
RAIZ = os.path.dirname(os.path.dirname(AQUI))
ENTRADA = os.path.join(RAIZ, "input", "interior-design.png")
SAIDA = os.path.join(RAIZ, "output")
BRUTO = os.path.join(SAIDA, "kling-respostas")
ANTES = os.path.join(SAIDA, "before-construction.png")
DEPOIS = os.path.join(SAIDA, "completed-interior.png")
VIDEO = os.path.join(SAIDA, "renovation-video.mp4")

# Medido em 2026-07-28: v3_0 foi o único dos três que manteve a janela e as
# paredes cegas. o1 ("edição precisa") e v3_0_omni recriaram o ambiente.
MODELO_IMG = "kling-image-v3_0"
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


def works_url(resp: dict) -> str:
    """URL do asset: `works[].url` (formato do query_tasks, ver GUIA-KLING-MCP-CLI)."""
    def procurar(o):
        if isinstance(o, dict):
            if isinstance(o.get("works"), list):
                for w in o["works"]:
                    if isinstance(w, dict) and w.get("url"):
                        return w["url"]
            for v in o.values():
                achado = procurar(v)
                if achado:
                    return achado
        elif isinstance(o, list):
            for v in o:
                achado = procurar(v)
                if achado:
                    return achado
        return None
    return procurar(resp)


def generation_id(resp: dict) -> str:
    bruto = json.dumps(resp)
    m = re.search(r'"generation_?[iI]d"\s*:\s*"?([\w-]+)', bruto)
    return m.group(1) if m else None


def resultado(resp: dict, rotulo: str, teto: int = 900) -> str:
    """Pega a URL do submit; se só veio o generation_id, faz poll no query_tasks.

    Nunca resubmete: job pago não cancela. Se não resolver, manda o usuário
    abrir a resposta bruta e baixar à mão.
    """
    url = works_url(resp)
    if url:
        return url
    gid = generation_id(resp)
    if not gid:
        raise RuntimeError(
            "sem works[].url e sem generation_id — abra o arquivo bruto em "
            f"{BRUTO} e baixe à mão (o job foi cobrado, NÃO resubmeta)"
        )
    print(f"[kling] generation_id={gid} — consultando query_tasks")
    inicio = time.time()
    while time.time() - inicio < teto:
        time.sleep(15)
        st = submeter(["kling", "query_tasks", gid], f"{rotulo}-query", timeout=120)
        url = works_url(st)
        print(f"[kling] {int(time.time() - inicio)}s {'pronto' if url else 'aguardando'}")
        if url:
            return url
    raise RuntimeError(
        f"timeout consultando {gid}. O job existe e foi cobrado — rode "
        f"`kling query_tasks {gid}` e baixe manualmente. NÃO resubmeta."
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
    # URLs do Kling expiram em 24h — baixar na hora
    return baixar(resultado(resp, "imagem"), ANTES)


def etapa_video(modelo: str, duracao: str, resolucao: str) -> str:
    # A API recusa: "720p is not supported with a tail image". O par A->B exige
    # o tier 1080p (pro) — mais crédito que o default 720p do klingai-nei.
    if resolucao != "1080p":
        print(f"[kling] ⚠️  {resolucao} não é aceito com tail image; subindo para "
              "1080p (tier pro, custa mais crédito)")
        resolucao = "1080p"
    resp = submeter(
        ["kling", "image_to_video", "--image", ANTES, "--tailImage", DEPOIS,
         "--model", modelo, "--duration", duracao, "--resolution", resolucao,
         "--imageCount", "1", "--poll", "900", prompts.VIDEO_SEEDANCE],
        rotulo="video", timeout=1200,
    )
    caminho = baixar(resultado(resp, "video"), VIDEO)
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
    ap.add_argument("--resolucao", default="1080p",
                    help="a API recusa 720p quando há tail image")
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
