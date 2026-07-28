---
name: virtual-staging-agnes
description: Cria um vídeo realista de reforma (virtual staging) a partir de UMA imagem de interior já pronto, com a API Agnes AI (custo US$ 0) — imagem "antes da obra" por img2img e time-lapse antes→depois por keyframes. É a skill DEFAULT para "vídeo de reforma", "virtual staging", "antes e depois de ambiente", "time-lapse de obra", "transformar foto de interior em vídeo de reforma", ou quando anexarem uma foto/render de interior pedindo o vídeo da transformação. Para o fluxo GPT Image + Higgsfield use virtual-staging-original; para Kling AI use virtual-staging-kling.
---

# Virtual Staging Video — Agnes AI (US$ 0)

> São **três skills irmãs**, uma por motor: `virtual-staging-agnes` (esta, sem custo),
> `virtual-staging-original` (GPT Image + Higgsfield MCP) e `virtual-staging-kling`
> (Kling AI, créditos pagos). Os prompts e o portão de consistência são os mesmos.

## Objetivo

A partir de **uma única imagem de interior finalizado**, produzir:

1. a imagem correspondente **antes da construção** (`agnes-image-2.1-flash`, img2img);
2. o **vídeo time-lapse de reforma** entre as duas imagens (`agnes-video-v2.0`, `mode:"keyframes"`).

## Como rodar

```bash
python3 agnes/rodar.py --so-imagem   # etapa 1: só o "antes" (portão de consistência)
python3 agnes/rodar.py --so-video    # etapa 2: o vídeo, reusando o "antes" aprovado
python3 agnes/rodar.py               # as duas de uma vez
```

## Escolha de provedor (por etapa, independentes)

| Flag | Opções | Default |
|---|---|---|
| `--img` | `agnes` (img2img HTTP) · `agente` (GPT Image, por handoff) | `agnes` |
| `--video` | `agnes` (keyframes HTTP) · `higgsfield` (Seedance 2.0 Mini via MCP, por handoff) | `agnes` |

```bash
python3 agnes/rodar.py                                  # tudo no Agnes (US$ 0)
python3 agnes/rodar.py --img agente --video agnes       # fallback do risco R1
python3 agnes/rodar.py --img agente --video higgsfield  # fluxo original
```

**Handoff:** GPT Image e Higgsfield são ferramentas do agente/MCP, não endpoints HTTP —
um script Python não os chama. Nesses ramos o script prepara os arquivos e escreve a
instrução exata (prompt + caminhos) em `output/HANDOFF-imagem.md` / `output/HANDOFF-video.md`;
**quem executa é você, o agente**. Leia o handoff, gere, salve no caminho indicado e siga.

No ramo `higgsfield`, confira `/mcp` antes: sem o MCP conectado, **pare e avise** — não
troque de gerador por conta própria.

Se o "antes" trocar a arquitetura, rode de novo passando o layout real do ambiente:

```bash
LAYOUT="one large window on the whole left wall, blank back wall with no openings, \
blank right wall with no openings" python3 agnes/rodar.py --so-imagem
```

## Arquivos do projeto

Entrada:

- `input/interior-design.png` (ou a imagem anexada no chat)

Saídas:

- `output/before-construction.png`
- `output/completed-interior.png`
- `output/renovation-video.mp4`

## Workflow

1. Localize a imagem de interior em `input/` (ou use a anexada no chat).
2. Analise a imagem e identifique: tipo de ambiente, posição da câmera, perspectiva, dimensões, paredes, janelas, portas e aberturas, pé-direito, piso, mobiliário, elementos embutidos, materiais, direção da luz e estilo de interiores.
3. Trate a imagem enviada como a referência **depois** (ambiente finalizado).
4. Gere a imagem **antes da construção** com GPT Image usando o prompt abaixo.
5. Preserve exatamente a arquitetura e a perspectiva de câmera.
6. Salve em `output/before-construction.png`.
7. Copie/salve a imagem enviada em `output/completed-interior.png`.
8. Use a imagem "antes" como `@image1`.
9. Use a imagem finalizada como `@image2`.
10. Gere o vídeo com Higgsfield Seedance 2.0 Mini (Higgsfield MCP) usando o prompt de vídeo abaixo.
11. Salve em `output/renovation-video.mp4`.

## Prompt — imagem antes da construção

Create a photorealistic before-construction version of the submitted completed interior.

Preserve exactly:

- the original camera position
- camera height
- lens perspective
- room dimensions
- ceiling height
- wall positions
- windows
- doors
- openings
- structural columns
- architectural geometry
- natural lighting direction

Remove:

- all furniture
- decoration
- finished flooring
- wall finishes
- built-in cabinets
- completed lighting fixtures
- luxury materials
- artwork
- accessories

Transform the room into a clean unfinished construction shell with raw cement or plaster walls, an unfinished ceiling, bare flooring, empty space, and simple natural daylight.

The output must look like the exact same room before renovation began.

Do not change the architecture.
Do not change the camera angle.
Do not add new doors or windows.
Do not add people.
Do not add furniture.
Do not add text or logos.
Avoid exposed loose wires and complicated construction machinery.

## Regras de consistência

As imagens antes e depois devem mostrar **o mesmo ambiente, da mesma câmera**.

Travar: ângulo de câmera, perspectiva, dimensões do ambiente, pé-direito, paredes, janelas, portas, aberturas, elementos estruturais.

Só podem mudar o estágio da obra e os acabamentos.

**Não prossiga para a geração de vídeo** se a imagem "antes" apresentar layout ou ângulo de câmera diferentes — regenere.

## Prompt — vídeo Seedance

Create a realistic time-lapse renovation transformation video with a locked camera, before: `@image1`, after: `@image2`, showing many renovation workers actively moving around the room wearing yellow safety helmets, orange reflective safety vests, work gloves, and construction boots.

Show fast-paced work such as measuring walls, carrying materials, drilling, plastering, painting, installing lights, laying flooring, mounting cabinets, moving ladders, cleaning dust, and assembling furniture.

As the time-lapse progresses, the unfinished room gradually transforms into a fully renovated modern interior, with raw cement walls becoming smooth finished walls, the exposed ceiling becoming a polished ceiling with lighting, bare floors becoming premium flooring, and the empty space filling with elegant built-ins and stylish furniture.

Keep the motion busy, realistic, and coordinated, with natural construction activity, dust movement, and a clear sense of progress throughout.

## Notas de API (medidas — ver `doc/PLANO-AGNES.md`)

- **Chave:** `AGNES_API_KEY` em `~/projetos/agnes-nei/.env`, lida em runtime. Nunca copiar nem imprimir.
- **Prompts em inglês** — em PT o filtro devolve HTTP 400 determinístico.
- **`size:"1312x736"` explícito, sem `ratio`** — no img2img o `ratio` é ignorado.
- **Vídeo:** `num_frames` segue 8n+1 e é ≤441 (18,4 s @24 fps); rate limit real de 5 req/min.
- **O JSON do vídeo mente sobre o tamanho:** pediu 1312×736 e o MP4 saiu 1280×704. Sempre conferir com `ffprobe` (o `rodar.py` já faz).
- **Sem `seed` no modelo de imagem** (o de vídeo tem) — o "antes" não é reproduzível; corrigir é regenerar.
- Saída padrão de artefatos: `output/` do projeto (ou `~/projetos/output/<projeto>/` quando pedido).
