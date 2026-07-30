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

## Quatro skills, um motor cada

| # | Skill | Imagem "antes" | Vídeo | Custo |
|---|---|---|---|---|
| 1 | `higgsfield` (original) | GPT Image (ferramenta do agente) | Higgsfield Seedance 2.0 Mini (MCP) | conforme a conta |
| 2 | `agnes` | `agnes-image-2.1-flash` (img2img) | `agnes-video-v2.0` (keyframes) | **US$ 0** |
| 3 | `kling` | `kling-image-v3_0` (ou `gpt-image2`) | `kling-video-v2_5` com `--tailImage` | **créditos Kling** |
| 4 | `codex-agnes` | Imagegen integrado à assinatura Codex | `agnes-video-v2.0` (3 segmentos) | limites Codex + Agnes grátis |

Medido em 2026-07-28, na mesma sala: **melhor vídeo = `kling`** (operários críveis, aterrissa no
keyframe B, mas com marca d'água KlingAI); **melhor custo = `agnes`** (US$ 0, operários borrados);
**melhor "antes" = `kling-image-v3_0`**.

Os fluxos curtos preservam o comportamento original. `agnes` e `codex-agnes`
também oferecem o pipeline em três partes, com aprovação opcional e portão de
consistência. Escolha pelo nome ao pedir.

```bash
python3 skills/agnes/rodar.py                          # Agnes completo (US$ 0)
python3 skills/agnes/rodar.py --img gpt-image2 --sim   # GPT Image 2 na imagem + vídeo Agnes
python3 skills/codex-agnes/rodar.py --help              # 3 imagens Codex + 3 vídeos Agnes
python3 skills/kling/rodar.py --sim                    # Kling nos dois (crédito)
python3 skills/higgsfield/rodar.py                     # prepara os handoffs do fluxo original
```

## Estrutura — quatro skills de vídeo

```text
vsvideo-skill/
├── input/interior-design.png     # a imagem do interior finalizado
├── output/                       # tudo que é gerado
├── skills/
│   ├── higgsfield/               # 1 — SKILL.md + rodar.py + prompts.py
│   ├── agnes/                    # 2 — inclui pipeline_18s.py compartilhado
│   ├── kling/                    # 3 — SKILL.md + rodar.py + prompts.py
│   └── codex-agnes/              # 4 — Imagegen Codex + vídeos Agnes
├── tests/                        # testes dos pipelines reutilizáveis
└── doc/                          # tutorial (PT/EN) + spec original + PLANO-AGNES.md
```

`higgsfield`, `agnes` e `kling` permanecem independentes. `codex-agnes` reutiliza
explicitamente o cliente e o pipeline de vídeo da skill `agnes`, mantendo toda a
lógica de virtual staging neste repositório.

## Instalação

Copie a pasta da skill para o diretório de skills do seu agente:

```bash
cp -r skills/{higgsfield,agnes,kling,codex-agnes} ~/.claude/skills/
```

Ou trabalhe direto dentro deste repo — o agente encontra a skill em `skills/`.

### Integração com InemacaBot

O InemacaBot aponta `VSV_SKILLS_ROOT` para a pasta `skills/` deste repositório.
O bot mantém somente autorização, comandos, filas, isolamento e entrega; os
entrypoints, prompts, validação e geração de mídia permanecem aqui.

```env
VSV_SKILLS_ROOT=/root/projetos/vsvideo-skill/skills
```

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

Trocando o nome, você escolhe o motor: `agnes`, `higgsfield`, `kling` ou
`codex-agnes`. Instaladas no diretório de skills, elas também respondem como
slash command:

```
/agnes
/higgsfield
/kling
/codex-agnes
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

### Origem da imagem dentro do Agnes

O vídeo é sempre Agnes; a imagem "antes" tem quatro origens:

| `--img` | Como funciona | Custo |
|---|---|---|
| `agnes` (default) | img2img da própria Agnes | **US$ 0** |
| `gpt-image2` | GPT Image 2 pelo CLI do Kling — gera lá, **baixa aqui** | crédito Kling |
| `kling` | `kling-image-v3_0` pelo CLI do Kling — idem | crédito Kling |
| `agente` | GPT Image do agente, por handoff | — |

As duas do meio só submetem com `--sim`.

```bash
LAYOUT="one large window on the whole left wall, blank back wall with no openings" \
  python3 skills/agnes/rodar.py --so-imagem
```

## Documentação

- `doc/SKILL.md` — especificação original (prompts completos).
- `doc/virtual_staging_renovation_video_pt.md` — tutorial em português.
- `doc/virtual_staging_renovation_video_en.md` — tutorial em inglês.

---

INEMA · [inema.club](https://inema.club)
