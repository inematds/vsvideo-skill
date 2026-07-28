#!/usr/bin/env python3
"""Sistema AGNES — independente. O VÍDEO é sempre Agnes (US$ 0); a imagem
"antes" pode vir de quatro origens.

    --img agnes       img2img da própria Agnes (default) — Agnes completo, US$ 0
    --img gpt-image2  GPT Image 2 pelo CLI do Kling — gera lá, BAIXA aqui (crédito Kling)
    --img kling       kling-image-v3_0 pelo CLI do Kling — gera lá, BAIXA aqui (crédito Kling)
    --img agente      GPT Image do agente, por handoff (sem custo de API)

Em todos os casos o vídeo é `agnes-video-v2.0` com `mode:"keyframes"`.

    python3 rodar.py                          # Agnes completo
    python3 rodar.py --img gpt-image2 --sim   # imagem no GPT Image 2 + vídeo Agnes
    python3 rodar.py --img kling --sim        # imagem no Kling + vídeo Agnes
    python3 rodar.py --so-imagem              # portão de consistência
    python3 rodar.py --so-video               # reusa o "antes" aprovado

Esta pasta é autossuficiente: client.py, prompts.py e rodar.py vivem aqui e não
dependem de skills/kling/ nem de skills/higgsfield/.
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

import client  # noqa: E402
import prompts  # noqa: E402

# raiz do projeto = duas pastas acima (skills/agnes/ -> repo/)
RAIZ = os.path.dirname(os.path.dirname(AQUI))
ENTRADA = os.path.join(RAIZ, "input", "interior-design.png")
SAIDA = os.path.join(RAIZ, "output")
BRUTO = os.path.join(SAIDA, "kling-respostas")
ANTES = os.path.join(SAIDA, "before-construction.png")
DEPOIS = os.path.join(SAIDA, "completed-interior.png")
VIDEO = os.path.join(SAIDA, "renovation-video.mp4")
HANDOFF_IMG = os.path.join(SAIDA, "HANDOFF-imagem.md")

LARGURA, ALTURA = 1312, 736
LIMITE_REF = 10 * 1024 * 1024  # 10 MB por imagem de referência (Agnes)

# modelos do CLI do Kling usados SÓ na etapa de imagem
MODELO_GPT = "gpt-image2"
MODELO_KLING = "kling-image-v3_0"


# ------------------------------------------------------------------ preparação

def preparar_entrada(origem: str) -> str:
    os.makedirs(SAIDA, exist_ok=True)
    shutil.copyfile(origem, DEPOIS)
    if os.path.getsize(DEPOIS) > LIMITE_REF:
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", origem,
             "-vf", f"scale={LARGURA}:{ALTURA}", DEPOIS],
            check=True,
        )
        print(f"[prep] redimensionada para {LARGURA}x{ALTURA} (limite de 10MB)")
    print(f"[prep] depois -> {DEPOIS} ({os.path.getsize(DEPOIS) // 1024} KB)")
    return DEPOIS


def prompt_antes() -> str:
    """Prompt do 'antes', com o layout real quando informado via LAYOUT=."""
    p = prompts.ANTES
    layout = os.environ.get("LAYOUT")
    if layout:
        p = p.replace(
            "It must look like the exact same room",
            f"Room layout, unchanged: {layout}. It must look like the exact same room",
        )
    return p


# ------------------------------------------------- etapa 1: imagem, 4 origens

def imagem_agnes() -> str:
    print("[1/2] 'antes' via Agnes img2img (US$ 0)")
    png = client.gerar_imagem(
        prompt_antes(), size=f"{LARGURA}x{ALTURA}", refs=[client.data_uri(DEPOIS)]
    )
    with open(ANTES, "wb") as fh:
        fh.write(png)
    print(f"[1/2] ok -> {ANTES} ({len(png) // 1024} KB)")
    return ANTES


def _works_url(o):
    if isinstance(o, dict):
        if isinstance(o.get("works"), list):
            for w in o["works"]:
                if isinstance(w, dict) and w.get("url"):
                    return w["url"]
        for v in o.values():
            achado = _works_url(v)
            if achado:
                return achado
    elif isinstance(o, list):
        for v in o:
            achado = _works_url(v)
            if achado:
                return achado
    return None


def _url_solta(texto: str):
    m = re.search(r"https?://[^\s\"']+\.(?:png|jpg|jpeg|webp)[^\s\"']*", texto)
    return m.group(0) if m else None


def imagem_via_kling(modelo: str) -> str:
    """Gera o 'antes' no CLI do Kling (gpt-image2 ou kling-image-*) e BAIXA aqui.

    Só a imagem passa pelo Kling; o vídeo continua no Agnes. Cobra crédito Kling.
    """
    if not shutil.which("kling"):
        raise RuntimeError("CLI `kling` não está no PATH (ver ~/projetos/klingaimcp)")
    os.makedirs(BRUTO, exist_ok=True)
    print(f"[1/2] 'antes' via CLI do Kling, modelo {modelo} (crédito Kling)")
    argv = ["kling", "image_to_image", "--image", DEPOIS, "--model", modelo,
            "--img_resolution", "1k", "--aspect_ratio", "16:9",
            "--imageCount", "1", "--poll", "300", prompt_antes()]
    proc = subprocess.run(argv, capture_output=True, text=True, timeout=420)
    carimbo = time.strftime("%Y%m%d-%H%M%S")
    caminho = os.path.join(BRUTO, f"imagem-{modelo}-{carimbo}.txt")
    with open(caminho, "w", encoding="utf-8") as fh:  # bruto ANTES de parsear
        fh.write(f"$ {' '.join(argv)}\n\n--- stdout ---\n{proc.stdout}\n"
                 f"--- stderr ---\n{proc.stderr}\n")
    print(f"[1/2] resposta bruta -> {caminho}")
    if proc.returncode != 0:
        raise RuntimeError(f"kling saiu com {proc.returncode}: {proc.stderr[:400]}")

    try:
        resp = json.loads(proc.stdout)
    except json.JSONDecodeError:
        resp = {"_texto": proc.stdout}
    url = _works_url(resp) or _url_solta(proc.stdout)
    if not url:
        raise RuntimeError(
            f"sem URL de resultado — abra {caminho} e baixe à mão "
            "(o job foi cobrado, NÃO resubmeta)"
        )
    # URLs do Kling expiram em 24h — baixar na hora
    with urllib.request.urlopen(url, timeout=600) as r, open(ANTES, "wb") as fh:
        fh.write(r.read())
    print(f"[1/2] baixado -> {ANTES} ({os.path.getsize(ANTES) // 1024} KB)")
    return ANTES


def imagem_agente() -> str:
    texto = f"""# Handoff — imagem "antes da construção" (GPT Image do agente)

**Referência (ambiente finalizado):** `{DEPOIS}`
**Salvar em:** `{ANTES}`  ·  **Proporção:** {LARGURA}x{ALTURA}

## Prompt

{prompt_antes()}

## Depois

Compare câmera e arquitetura com a referência; se o layout mudou, gere de novo.
Depois rode: `python3 skills/agnes/rodar.py --so-video`
"""
    with open(HANDOFF_IMG, "w", encoding="utf-8") as fh:
        fh.write(texto)
    print(f"[1/2] handoff -> {HANDOFF_IMG}")
    return HANDOFF_IMG


# ---------------------------------------------------- etapa 2: vídeo (Agnes)

def etapa_video(num_frames: int, seed: int) -> str:
    print(f"[2/2] vídeo via Agnes, keyframes ({num_frames} frames @24fps, US$ 0)")
    mp4 = client.gerar_video(
        prompts.VIDEO,
        keyframes=[client.data_uri(ANTES), client.data_uri(DEPOIS)],
        num_frames=num_frames, frame_rate=24,
        width=LARGURA, height=ALTURA, seed=seed,
    )
    with open(VIDEO, "wb") as fh:
        fh.write(mp4)
    print(f"[2/2] ok -> {VIDEO} ({len(mp4) // 1024} KB)")
    print(f"[ffprobe] {ffprobe(VIDEO)}")  # o JSON da API mente sobre o tamanho
    return VIDEO


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
    ap.add_argument("--img", default="agnes",
                    choices=("agnes", "gpt-image2", "kling", "agente"),
                    help="origem da imagem 'antes' — o vídeo é sempre Agnes")
    ap.add_argument("--modelo-kling", default=MODELO_KLING,
                    help="com --img kling: kling-image-v3_0 | kling-image-o1 | …")
    ap.add_argument("--frames", type=int, default=145, help="8n+1, <=441")
    ap.add_argument("--seed", type=int, default=70428)
    ap.add_argument("--so-imagem", action="store_true")
    ap.add_argument("--so-video", action="store_true")
    ap.add_argument("--sim", action="store_true",
                    help="confirma gasto de crédito Kling (só para --img gpt-image2|kling)")
    args = ap.parse_args()

    print(f"[cfg] imagem={args.img} · vídeo=agnes")

    if not args.so_video:
        if not os.path.exists(args.imagem):
            print(f"erro: imagem não encontrada em {args.imagem}")
            return 1
        preparar_entrada(args.imagem)

        if args.img in ("gpt-image2", "kling") and not args.sim:
            print("\n⚠️  Essa origem passa pelo CLI do Kling e É COBRADA em créditos.")
            print("    Repita com --sim para submeter.")
            return 2

        if args.img == "agnes":
            imagem_agnes()
        elif args.img == "gpt-image2":
            imagem_via_kling(MODELO_GPT)
        elif args.img == "kling":
            imagem_via_kling(args.modelo_kling)
        else:
            imagem_agente()
            print("\nGere o 'antes' e depois rode: python3 skills/agnes/rodar.py --so-video")
            return 0

        if args.so_imagem:
            print("\nConfira o 'antes': mesma câmera, mesmas paredes e aberturas. "
                  "Se o layout mudou, rode de novo (use LAYOUT=…).")
            return 0

    for arquivo in (ANTES, DEPOIS):
        if not os.path.exists(arquivo):
            print(f"erro: o vídeo precisa de {arquivo}")
            return 1
    etapa_video(args.frames, args.seed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
