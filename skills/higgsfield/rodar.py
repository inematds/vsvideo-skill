#!/usr/bin/env python3
"""Sistema HIGGSFIELD — independente. Fluxo original: GPT Image na imagem,
Higgsfield Seedance 2.0 Mini no vídeo.

Nenhuma das duas etapas é HTTP: as duas são ferramentas do agente/MCP. Então
este script NÃO gera nada — ele prepara os arquivos e escreve os handoffs com
prompt e caminhos prontos, e **o agente executa**.

    python3 rodar.py               # prepara os dois handoffs
    python3 rodar.py --so-imagem   # só o handoff da imagem

Esta pasta é autossuficiente: prompts.py e rodar.py vivem aqui.
"""

import argparse
import os
import shutil
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import prompts  # noqa: E402  (cópia local)

# raiz do projeto = duas pastas acima (skills/higgsfield/ -> repo/)
RAIZ = os.path.dirname(os.path.dirname(AQUI))
ENTRADA = os.path.join(RAIZ, "input", "interior-design.png")
SAIDA = os.path.join(RAIZ, "output")
ANTES = os.path.join(SAIDA, "before-construction.png")
DEPOIS = os.path.join(SAIDA, "completed-interior.png")
VIDEO = os.path.join(SAIDA, "renovation-video.mp4")
HANDOFF_IMG = os.path.join(SAIDA, "HANDOFF-imagem.md")
HANDOFF_VID = os.path.join(SAIDA, "HANDOFF-video.md")

LARGURA, ALTURA = 1312, 736


def prompt_antes() -> str:
    p = prompts.ANTES
    layout = os.environ.get("LAYOUT")
    if layout:
        p = p.replace(
            "It must look like the exact same room",
            f"Room layout, unchanged: {layout}. It must look like the exact same room",
        )
    return p


def handoff_imagem() -> str:
    texto = f"""# Handoff — imagem "antes da construção" (GPT Image)

**Você**, agente, executa: o GPT Image é ferramenta sua, não endpoint HTTP.

**Referência (ambiente finalizado):** `{DEPOIS}`
**Salvar em:** `{ANTES}`  ·  **Proporção:** {LARGURA}x{ALTURA} (16:9)

## Prompt

{prompt_antes()}

## Portão de consistência

Compare as duas: mesma câmera, mesmas paredes, mesmas aberturas, mesmo pé-direito.
Se o layout mudou, **regenere** — não leve um "antes" errado para o vídeo.
"""
    with open(HANDOFF_IMG, "w", encoding="utf-8") as fh:
        fh.write(texto)
    print(f"[1/2] handoff -> {HANDOFF_IMG}")
    return HANDOFF_IMG


def handoff_video() -> str:
    texto = f"""# Handoff — vídeo de reforma (Higgsfield Seedance 2.0 Mini, via MCP)

**Você**, agente, executa: o Higgsfield é MCP, não endpoint HTTP. Confirme antes
com `/mcp` que ele está conectado — sem isso, **pare e avise**, não troque de
gerador por conta própria (para isso existem as skills `agnes` e `kling`).

**@image1 (antes):** `{ANTES}`
**@image2 (depois):** `{DEPOIS}`
**Salvar em:** `{VIDEO}`  ·  **Modelo:** Seedance 2.0 Mini

## Prompt

{prompts.VIDEO_SEEDANCE}

## Depois

Confira o arquivo com `ffprobe` (dimensão e duração reais), não o JSON da resposta.
"""
    with open(HANDOFF_VID, "w", encoding="utf-8") as fh:
        fh.write(texto)
    print(f"[2/2] handoff -> {HANDOFF_VID}")
    return HANDOFF_VID


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--imagem", default=ENTRADA)
    ap.add_argument("--so-imagem", action="store_true")
    ap.add_argument("--so-video", action="store_true")
    args = ap.parse_args()

    os.makedirs(SAIDA, exist_ok=True)
    if not args.so_video:
        if not os.path.exists(args.imagem):
            print(f"erro: imagem não encontrada em {args.imagem}")
            return 1
        shutil.copyfile(args.imagem, DEPOIS)
        print(f"[prep] depois -> {DEPOIS} ({os.path.getsize(DEPOIS) // 1024} KB)")
        handoff_imagem()
        if args.so_imagem:
            return 0
    handoff_video()
    print("\nOs dois handoffs estão em output/. O agente executa a partir deles.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
