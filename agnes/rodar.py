#!/usr/bin/env python3
"""Pipeline: interior finalizado -> imagem 'antes' -> vídeo de reforma.

Cada etapa escolhe o seu provedor, de forma independente:

    --img    agnes | agente     (default: agnes)
    --video  agnes | higgsfield (default: agnes)

`agnes` = HTTP direto, o script resolve sozinho (custo US$ 0).
`agente`/`higgsfield` = handoff: o script prepara os arquivos e escreve a
instrução exata em output/HANDOFF-<etapa>.md; quem executa é o agente, porque
GPT Image e o Higgsfield MCP são ferramentas dele, não endpoints HTTP.

Exemplos:
    python3 agnes/rodar.py                                  # tudo no Agnes
    python3 agnes/rodar.py --so-imagem                      # portão de consistência
    python3 agnes/rodar.py --img agente --video agnes       # fallback do risco R1
    python3 agnes/rodar.py --img agente --video higgsfield  # fluxo original
"""

import argparse
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import client  # noqa: E402
import prompts  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENTRADA = os.path.join(RAIZ, "input", "interior-design.png")
SAIDA = os.path.join(RAIZ, "output")
ANTES = os.path.join(SAIDA, "before-construction.png")
DEPOIS = os.path.join(SAIDA, "completed-interior.png")
VIDEO = os.path.join(SAIDA, "renovation-video.mp4")
HANDOFF_IMG = os.path.join(SAIDA, "HANDOFF-imagem.md")
HANDOFF_VID = os.path.join(SAIDA, "HANDOFF-video.md")

LARGURA, ALTURA = 1312, 736
LIMITE_REF = 10 * 1024 * 1024  # 10 MB por imagem de referência (Agnes)


# ---------------------------------------------------------------- preparação

def preparar_entrada(origem: str) -> str:
    """Copia a imagem enviada como 'depois' e garante <=10MB / 1312x736."""
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
    """Prompt do 'antes', com o layout real do ambiente quando informado.

    Sem isso o img2img inventa portas e janelas (PLANO-AGNES.md, risco R1).
    """
    p = prompts.ANTES
    layout = os.environ.get("LAYOUT")
    if layout:
        p = p.replace(
            "It must look like the exact same room",
            f"Room layout, unchanged: {layout}. It must look like the exact same room",
        )
    return p


# ------------------------------------------------------- etapa 1: a imagem

def imagem_agnes() -> str:
    print("[1/2] 'antes da obra' via Agnes (img2img)")
    png = client.gerar_imagem(
        prompt_antes(),
        size=f"{LARGURA}x{ALTURA}",
        refs=[client.data_uri(DEPOIS)],
    )
    with open(ANTES, "wb") as fh:
        fh.write(png)
    print(f"[1/2] ok -> {ANTES} ({len(png) // 1024} KB) {dimensao(ANTES)}")
    return ANTES


def imagem_agente() -> str:
    """Handoff para o agente gerar o 'antes' com GPT Image (fluxo original)."""
    texto = f"""# Handoff — imagem "antes da construção" (GPT Image)

O script preparou o material. **Você**, agente, executa esta etapa: o GPT Image é
ferramenta sua, não endpoint HTTP.

**Referência (o ambiente finalizado):** `{DEPOIS}`
**Salvar o resultado em:** `{ANTES}`
**Proporção:** {LARGURA}x{ALTURA} (16:9)

## Prompt

{prompt_antes()}

## Depois de gerar

Compare as duas imagens e só siga se a **câmera e a arquitetura** baterem: mesma
posição e altura de câmera, mesmas paredes, mesmas aberturas, mesmo pé-direito.
Se o layout mudou, gere de novo — não leve um "antes" errado para o vídeo.

Em seguida rode a etapa 2:

```bash
python3 agnes/rodar.py --so-video --video agnes        # ou --video higgsfield
```
"""
    with open(HANDOFF_IMG, "w", encoding="utf-8") as fh:
        fh.write(texto)
    print(f"[1/2] handoff -> {HANDOFF_IMG}")
    print("[1/2] o agente gera o 'antes' com GPT Image e salva em output/.")
    return HANDOFF_IMG


# -------------------------------------------------------- etapa 2: o vídeo

def video_agnes(num_frames: int, seed: int) -> str:
    print(f"[2/2] vídeo via Agnes ({num_frames} frames @24fps)")
    mp4 = client.gerar_video(
        prompts.VIDEO,
        keyframes=[client.data_uri(ANTES), client.data_uri(DEPOIS)],
        num_frames=num_frames,
        frame_rate=24,
        width=LARGURA,
        height=ALTURA,
        seed=seed,
    )
    with open(VIDEO, "wb") as fh:
        fh.write(mp4)
    print(f"[2/2] ok -> {VIDEO} ({len(mp4) // 1024} KB)")
    # o JSON da API mente sobre o tamanho — medir o arquivo de verdade
    print(f"[ffprobe] {ffprobe(VIDEO)}")
    return VIDEO


def video_higgsfield() -> str:
    """Handoff para o agente gerar o vídeo pelo Higgsfield MCP (fluxo original)."""
    texto = f"""# Handoff — vídeo de reforma (Higgsfield Seedance 2.0 Mini, via MCP)

O script preparou os keyframes. **Você**, agente, executa esta etapa: o Higgsfield
é MCP, não endpoint HTTP. Confirme antes com `/mcp` que ele está conectado — sem
isso, pare e avise, não troque de gerador por conta própria.

**@image1 (antes):** `{ANTES}`
**@image2 (depois):** `{DEPOIS}`
**Salvar em:** `{VIDEO}`
**Modelo:** Seedance 2.0 Mini

## Prompt

{prompts.VIDEO_SEEDANCE}

## Depois de gerar

Confira o arquivo com `ffprobe` (dimensão e duração reais), não o JSON da resposta.
"""
    with open(HANDOFF_VID, "w", encoding="utf-8") as fh:
        fh.write(texto)
    print(f"[2/2] handoff -> {HANDOFF_VID}")
    print("[2/2] o agente dispara o Higgsfield MCP com os dois keyframes.")
    return HANDOFF_VID


# ------------------------------------------------------------------ utilidades

def dimensao(caminho: str) -> str:
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height", "-of", "csv=p=0:s=x", caminho],
            capture_output=True, text=True, check=True,
        )
        return out.stdout.strip()
    except Exception as e:  # ffprobe ausente não deve derrubar o pipeline
        return f"(ffprobe indisponível: {e})"


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
    ap.add_argument("--imagem", default=ENTRADA, help="interior finalizado")
    ap.add_argument("--img", choices=("agnes", "agente"), default="agnes",
                    help="provedor da imagem 'antes' (agente = GPT Image, por handoff)")
    ap.add_argument("--video", choices=("agnes", "higgsfield"), default="agnes",
                    help="provedor do vídeo (higgsfield = MCP, por handoff)")
    ap.add_argument("--frames", type=int, default=145, help="8n+1, <=441")
    ap.add_argument("--seed", type=int, default=70428)
    ap.add_argument("--so-imagem", action="store_true")
    ap.add_argument("--so-video", action="store_true")
    args = ap.parse_args()

    print(f"[cfg] imagem={args.img} · vídeo={args.video}")

    if not args.so_video:
        if not os.path.exists(args.imagem):
            print(f"erro: imagem não encontrada em {args.imagem}")
            return 1
        preparar_entrada(args.imagem)
        if args.img == "agnes":
            imagem_agnes()
        else:
            imagem_agente()
            print("\nGere o 'antes' e depois rode a etapa 2 com --so-video.")
            return 0
        if args.so_imagem:
            print("\nConfira o 'antes' antes de gerar o vídeo: mesma câmera, "
                  "mesmas paredes e aberturas. Se o layout mudou, rode de novo.")
            return 0

    for arquivo in (ANTES, DEPOIS):
        if not os.path.exists(arquivo):
            print(f"erro: o vídeo precisa de {arquivo} — gere a etapa 1 antes")
            return 1

    if args.video == "agnes":
        video_agnes(args.frames, args.seed)
    else:
        video_higgsfield()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
