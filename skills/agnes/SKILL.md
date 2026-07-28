---
name: agnes
description: Cria um vídeo realista de reforma (virtual staging) a partir de UMA imagem de interior já pronto, com a API Agnes AI (custo US$ 0) — imagem "antes da obra" por img2img e time-lapse antes→depois por keyframes. É a skill DEFAULT para "vídeo de reforma", "virtual staging", "antes e depois de ambiente", "time-lapse de obra", "transformar foto de interior em vídeo de reforma", ou quando anexarem uma foto/render de interior pedindo o vídeo da transformação. Para o fluxo GPT Image + Higgsfield use higgsfield; para Kling AI use kling.
---

# Virtual Staging Video — Agnes AI (US$ 0)

> **Três sistemas independentes**, um por pasta: `skills/higgsfield/`, `skills/agnes/` (esta)
> e `skills/kling/`. Cada uma tem o próprio `rodar.py` e `prompts.py` — mexer numa não afeta
> as outras. Esta é a única sem custo de API.

## Objetivo

A partir de **uma única imagem de interior finalizado**, produzir:

1. a imagem correspondente **antes da construção** (`agnes-image-2.1-flash`, img2img);
2. o **vídeo time-lapse de reforma** entre as duas imagens (`agnes-video-v2.0`, `mode:"keyframes"`).

## Como rodar (tudo dentro desta pasta)

```bash
python3 skills/agnes/rodar.py                          # Agnes COMPLETO (imagem + vídeo, US$ 0)
python3 skills/agnes/rodar.py --img gpt-image2 --sim   # imagem no GPT Image 2 + vídeo Agnes
python3 skills/agnes/rodar.py --img kling --sim        # imagem no Kling + vídeo Agnes
python3 skills/agnes/rodar.py --so-imagem              # portão de consistência
python3 skills/agnes/rodar.py --so-video               # reusa o "antes" aprovado
```

## Origem da imagem "antes" (o vídeo é SEMPRE Agnes)

| `--img` | Como funciona | Custo |
|---|---|---|
| `agnes` (default) | img2img da própria Agnes | **US$ 0** |
| `gpt-image2` | GPT Image 2 pelo CLI do Kling; o script **gera lá e baixa aqui** | crédito Kling |
| `kling` | `kling-image-v3_0` (ou `--modelo-kling`) pelo CLI do Kling, idem | crédito Kling |
| `agente` | GPT Image do agente, por handoff em `output/HANDOFF-imagem.md` | — |

As origens `gpt-image2` e `kling` **só submetem com `--sim`** — passam pelo CLI do Kling, que
cobra crédito. A resposta bruta fica em `output/kling-respostas/` e a imagem é baixada na
hora (URLs do Kling expiram em 24 h).

Se o "antes" trocar a arquitetura, repita com o layout real:

```bash
LAYOUT="one large window on the whole left wall, blank back wall with no openings" \
  python3 skills/agnes/rodar.py --so-imagem
```

## Notas de API (medidas — ver `doc/PLANO-AGNES.md`)

- **Chave:** `AGNES_API_KEY` em `~/projetos/agnes-nei/.env`, lida em runtime. Nunca copiar nem imprimir.
- **Prompts em inglês** — em PT o filtro devolve HTTP 400 determinístico.
- **`size:"1312x736"` explícito, sem `ratio`** — no img2img o `ratio` é ignorado.
- **Vídeo:** `num_frames` segue 8n+1 e é ≤441 (18,4 s @24 fps); rate limit real de 5 req/min.
- **O JSON do vídeo mente sobre o tamanho:** pediu 1312×736 e o MP4 saiu 1280×704. Sempre conferir com `ffprobe` (o `rodar.py` já faz).
- **Sem `seed` no modelo de imagem** (o de vídeo tem) — o "antes" não é reproduzível; corrigir é regenerar.
- Saída padrão de artefatos: `output/` do projeto (ou `~/projetos/output/<projeto>/` quando pedido).
