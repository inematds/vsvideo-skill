# vsvideo-skill — Virtual Staging Video

## 📖 Guia de uso

Guia completo (landing + passo a passo): **https://inematds.github.io/vsvideo-skill/guia/**

---

Skill que transforma **uma foto/render de interior finalizado** num **vídeo time-lapse de reforma** (antes → depois), sem edição manual.

## Como funciona

1. Analisa a imagem enviada (câmera, perspectiva, arquitetura, materiais, luz, estilo).
2. Gera a versão **antes da construção** do mesmo ambiente — mesma câmera, mesma arquitetura, só o acabamento muda.
3. Valida a consistência (ângulo/layout). Se divergir, regenera — antes de gastar a etapa cara.
4. Gera o **vídeo de reforma** interpolando "antes" → "depois" como par de keyframes.

O motor de cada etapa depende da skill escolhida (tabela abaixo).

## Três skills, um motor cada

| # | Skill | Imagem "antes" | Vídeo | Custo |
|---|---|---|---|---|
| 1 | `higgsfield` (original) | GPT Image (ferramenta do agente) | Higgsfield Seedance 2.0 Mini (MCP) | conforme a conta |
| 2 | `agnes` | `agnes-image-2.1-flash` (img2img) | `agnes-video-v2.0` (keyframes) | **US$ 0** |
| 3 | `kling` | `kling-image-v3_0` (ou `gpt-image2`) | `kling-video-v2_5` com `--tailImage` | **créditos Kling** |

Medido em 2026-07-28, na mesma sala: **melhor vídeo = `kling`** (operários críveis, aterrissa no
keyframe B, mas com marca d'água KlingAI); **melhor custo = `agnes`** (US$ 0, operários borrados);
**melhor "antes" = `kling-image-v3_0`**.

Prompts, portão de consistência e caminhos de saída são idênticos nas três — o que muda é o
motor. Escolha pelo nome ao pedir ("faz o vídeo de reforma pelo Kling").

```bash
python3 agnes/rodar.py                    # Agnes: sem custo, roda direto
python3 kling/rodar.py --so-imagem --sim  # Kling: só submete com --sim (é cobrado)
```

## Estrutura

```text
vsvideo-skill/
├── input/                       # coloque aqui a imagem do interior
│   └── interior-design.png
├── output/                      # gerados
│   ├── before-construction.png
│   ├── completed-interior.png
│   └── renovation-video.mp4
├── agnes/                       # motor Agnes (HTTP, US$ 0) + prompts compartilhados
├── kling/                       # motor Kling (CLI `kling`, créditos pagos)
├── skills/
│   ├── higgsfield/SKILL.md      # 1 — fluxo original (GPT Image + Seedance)
│   ├── agnes/SKILL.md           # 2 — Agnes AI (US$ 0)
│   └── kling/SKILL.md           # 3 — Kling AI (créditos)
└── doc/                         # tutorial (PT/EN) + spec original
```

## Instalação

Copie a pasta da skill para o diretório de skills do seu agente:

```bash
cp -r skills/{higgsfield,agnes,kling} ~/.claude/skills/
```

Ou trabalhe direto dentro deste repo — o agente encontra a skill em `skills/`.

## Uso

Três formas de dar o comando.

### 1. Linguagem natural (o normal)

```bash
cd ~/projetos/vsvideo-skill
cp ~/Downloads/sala.png input/interior-design.png
claude
```

E, no chat:

> faz o vídeo de reforma dessa imagem

Gatilhos que acionam a skill: *vídeo de reforma*, *virtual staging*, *antes e depois do ambiente*, *time-lapse de obra*, *transformar foto de interior em vídeo de reforma*.

### 2. Anexando a imagem no chat

Sem usar `input/` — arraste a imagem e peça:

> [imagem anexada] transforma isso num vídeo de reforma

### 3. Forçando a skill pelo nome

Quando não quiser depender do gatilho:

> usa a skill agnes na imagem em input/interior-design.png

Trocando o nome, você escolhe o motor: `agnes`, `higgsfield`
ou `kling`. Instaladas em `~/.claude/skills/`, as três também respondem como
slash command:

```
/agnes
/higgsfield
/kling
```

Antes de rodar: em `/higgsfield`, confira o MCP com `/mcp` — sem o Higgsfield conectado a skill
para nas duas imagens. Em `/kling`, lembre que cada submissão gasta crédito.

Saídas em `output/`:

```text
output/before-construction.png   # casca de obra
output/completed-interior.png    # o ambiente pronto
output/renovation-video.mp4      # o time-lapse
```

## Pré-requisitos

- `AGNES_API_KEY` em `~/projetos/agnes-nei/.env` (API Agnes AI, custo US$ 0).
- `ffmpeg` / `ffprobe` no PATH.
- Python 3 (só a biblioteca padrão — sem dependências).

Modelos usados: `agnes-image-2.1-flash` (img2img, imagem "antes") e `agnes-video-v2.0`
(`mode:"keyframes"`, vídeo antes→depois).

> ⚠️ No plano free da Agnes, seus dados podem ser usados para treinar os modelos.
> Não envie imagem de cliente que seja confidencial.

### Rodando pelo script

```bash
python3 agnes/rodar.py --so-imagem   # etapa 1: só o "antes" (portão de consistência)
python3 agnes/rodar.py --so-video    # etapa 2: o vídeo, reusando o "antes" aprovado
python3 agnes/rodar.py               # as duas de uma vez
```

### Escolhendo o provedor de cada etapa

As duas etapas são independentes:

| Flag | Opções | Default |
|---|---|---|
| `--img` | `agnes` (img2img HTTP) · `agente` (GPT Image, por handoff) | `agnes` |
| `--video` | `agnes` (keyframes HTTP) · `higgsfield` (Seedance 2.0 Mini via MCP, por handoff) | `agnes` |

```bash
python3 agnes/rodar.py                                  # tudo no Agnes (US$ 0)
python3 agnes/rodar.py --img agente --video agnes       # GPT Image + vídeo Agnes
python3 agnes/rodar.py --img agente --video higgsfield  # fluxo original
```

Nos ramos `agente`/`higgsfield` o script não chama a API — GPT Image e Higgsfield são
ferramentas do agente/MCP. Ele prepara os arquivos e escreve a instrução em
`output/HANDOFF-imagem.md` / `output/HANDOFF-video.md`, e o agente executa a partir dali.
Assim o fluxo original continua funcionando, sem nada removido.

Se o "antes" trocar a arquitetura, repita descrevendo o layout real:

```bash
LAYOUT="one large window on the whole left wall, blank back wall with no openings" \
  python3 agnes/rodar.py --so-imagem
```

## Documentação

- `doc/SKILL.md` — especificação original (prompts completos).
- `doc/virtual_staging_renovation_video_pt.md` — tutorial em português.
- `doc/virtual_staging_renovation_video_en.md` — tutorial em inglês.

---

INEMA · [inema.club](https://inema.club)
