---
name: virtual-staging-kling
description: Vídeo de reforma (virtual staging) a partir de UMA imagem de interior pronto, usando o Kling AI para as duas etapas — imagem "antes da obra" com image_to_image (kling-image-o1) e time-lapse antes→depois com image_to_video usando --tailImage. Use quando pedirem o vídeo de reforma "pelo Kling", "com Kling AI", ou quando quiserem a melhor fidelidade de edição e aceitarem gastar créditos. Para a versão sem custo use virtual-staging-agnes; para GPT Image + Higgsfield use virtual-staging-original.
---

# Virtual Staging Video — Kling AI

Motor: `kling/rodar.py`, sobre o CLI `kling` (repo `klingaimcp`).

> ⚠️ **Toda submissão é cobrada em créditos** da conta Pro/SVIP e **não cancela**.
> O script não envia nada sem `--sim`. Nunca submeta job de teste às cegas; confirme os
> modelos com o usuário antes.

## Por que Kling aqui

- `image_to_video` aceita **`--tailImage`** — o par A→B nativo, exatamente o "antes/depois".
- `image_to_image` tem o **`kling-image-o1`** ("consistência de features, edição precisa"),
  que é o modelo que mais se aproxima de *editar* o ambiente em vez de reinterpretá-lo —
  o ponto fraco do Agnes (ver `doc/PLANO-AGNES.md`, risco R1).
- O mesmo CLI ainda expõe `gpt-image2`, `gemini-3-pro-image` e outros como modelo de imagem.

## Duas portas para a mesma conta

| Porta | Autenticação | Quando usar |
|---|---|---|
| **CLI `kling`** (default) | token em `~/.kling/.credentials` (`kling login`, OAuth) | scriptável — é o que o `kling/rodar.py` usa; funciona headless |
| **MCP `klingai`** | OAuth do kling.ai (`https://kling.ai/mcp`) | no chat, quando você quiser disparar pelas ferramentas do agente |

O `.mcp.json` do repo já declara o `klingai`; ao abrir a sessão neste projeto, confirme com
`/mcp` (pode pedir reautorização). **Não há chave de API em `.env`** — nem no `wifi` nem no
`openpcbot`; as duas portas usam login OAuth da mesma conta Pro/SVIP.

⚠️ MCP com autenticação interativa costuma **não** estar disponível em execução headless/cron.
Para automação, use o CLI.

## Como rodar

```bash
python3 kling/rodar.py --so-imagem --sim   # etapa 1 (portão de consistência)
python3 kling/rodar.py --so-video  --sim   # etapa 2, reusando o "antes" aprovado
python3 kling/rodar.py --sim               # as duas
```

Sem `--sim` o script só imprime a configuração e sai com código 2 — é o freio de crédito.

| Flag | Default | Opções |
|---|---|---|
| `--modelo-img` | `kling-image-o1` | `kling-image-v3_0_omni`, `kling-image-v3_0`, `gpt-image2`, `gemini-3-pro-image`, `gemini-3.1-flash-image`, `kling-image-v2_1` |
| `--modelo-video` | `kling-video-v2_5` | `kling-video-v2_6`, `kling-video-v3_0_turbo`, `kling-video-v3_0`, `kling-video-v3_0_omni`, `kling-video-o1` |
| `--duracao` | `5` | `5`, `10` (segundos) |
| `--resolucao` | `720p` | default do Nei — 1080p/4k só sob pedido explícito |

Se o "antes" trocar a arquitetura, repita descrevendo o layout real:

```bash
LAYOUT="one large window on the whole left wall, blank back wall with no openings" \
  python3 kling/rodar.py --so-imagem --sim
```

## Regras do motor

- **Resposta bruta gravada antes de qualquer parse**, em `output/kling-respostas/` — job pago
  não cancela e ID perdido é crédito perdido (regra do `klingai-nei`).
- O resultado sai em **`works[].url`**; se o submit só devolver `generation_id`, o script faz
  poll em `kling query_tasks <id>`.
- **As URLs expiram em 24 h** — o script baixa na hora. Se o download falhar, recupere com
  `kling query_tasks <generation_id>` (o arquivo bruto guarda o id).
- Se o script não achar a URL do resultado, ele **não resubmete**: manda você abrir o arquivo
  bruto e baixar à mão. Resubmeter às cegas gasta crédito de novo.
- **Prompts em inglês** (compartilhados com as outras skills, em `agnes/prompts.py`); o de
  vídeo usado aqui é o `VIDEO_SEEDANCE`, com os operários em primeiro plano.
- Conferir o MP4 com `ffprobe` (o script já faz), não o JSON da resposta.

## Portão de consistência

Antes de gastar crédito no vídeo, compare "antes" e "depois": mesma câmera, mesmas paredes,
mesmas aberturas, mesmo pé-direito. Se o layout mudou, regenere a imagem — não leve um
"antes" errado para a etapa cara.
