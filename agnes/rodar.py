#!/usr/bin/env python3
"""Pipeline Agnes: interior finalizado -> imagem 'antes' -> vídeo de reforma.

    python3 agnes/rodar.py                    # tudo
    python3 agnes/rodar.py --so-imagem        # só a etapa 1 (portão de consistência)
    python3 agnes/rodar.py --so-video         # reaproveita o 'antes' já gerado
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

LARGURA, ALTURA = 1312, 736
LIMITE_REF = 10 * 1024 * 1024  # 10 MB por imagem de referência


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


def etapa_imagem() -> str:
    print("[1/2] gerando o 'antes da obra' (img2img)")
    prompt = prompts.ANTES
    if os.environ.get("LAYOUT"):
        # descrição do layout real, extraída da análise da imagem — reduz a
        # deriva de arquitetura do img2img (ver PLANO-AGNES.md, risco R1)
        prompt = prompt.replace(
            "It must look like the exact same room",
            f"Room layout, unchanged: {os.environ['LAYOUT']}. "
            "It must look like the exact same room",
        )
    png = client.gerar_imagem(
        prompt,
        size=f"{LARGURA}x{ALTURA}",
        refs=[client.data_uri(DEPOIS)],
    )
    with open(ANTES, "wb") as fh:
        fh.write(png)
    print(f"[1/2] ok -> {ANTES} ({len(png) // 1024} KB) {dimensao(ANTES)}")
    return ANTES


def etapa_video(num_frames: int, seed: int) -> str:
    print(f"[2/2] gerando o vídeo ({num_frames} frames @24fps)")
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
    ap.add_argument("--frames", type=int, default=145, help="8n+1, <=441")
    ap.add_argument("--seed", type=int, default=70428)
    ap.add_argument("--so-imagem", action="store_true")
    ap.add_argument("--so-video", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(args.imagem):
        print(f"erro: imagem não encontrada em {args.imagem}")
        return 1

    if not args.so_video:
        preparar_entrada(args.imagem)
        etapa_imagem()
        if args.so_imagem:
            print("\nConfira o 'antes' antes de gerar o vídeo: mesma câmera, "
                  "mesmas paredes e aberturas. Se o layout mudou, rode de novo.")
            return 0
    elif not os.path.exists(ANTES):
        print(f"erro: --so-video exige {ANTES} já gerado")
        return 1

    etapa_video(args.frames, args.seed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
