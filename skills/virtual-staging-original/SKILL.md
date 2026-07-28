---
name: virtual-staging-original
description: Vídeo de reforma (virtual staging) a partir de UMA imagem de interior pronto, pelo fluxo ORIGINAL — imagem "antes da obra" com GPT Image e time-lapse antes→depois com Higgsfield Seedance 2.0 Mini via MCP. Use quando pedirem o vídeo de reforma "pelo Higgsfield", "pelo Seedance", "com GPT Image", ou o "fluxo original". Para a versão sem custo use virtual-staging-agnes; para a versão Kling use virtual-staging-kling.
---

# Virtual Staging Video — fluxo original (GPT Image + Higgsfield)

Este é o fluxo da spec original (`doc/SKILL.md`), preservado sem alterações de comportamento.
Nenhuma etapa é HTTP: as duas usam **ferramentas do agente/MCP**, então **você** executa.

## Antes de começar

Confira com `/mcp` que o **Higgsfield MCP** está conectado. **Se não estiver, pare e avise
o usuário** — não substitua por outro gerador por conta própria (para isso existem as
skills `virtual-staging-agnes` e `virtual-staging-kling`, e a troca é decisão do usuário).

## Arquivos

Entrada: `input/interior-design.png` (ou a imagem anexada no chat)
Saídas: `output/before-construction.png` · `output/completed-interior.png` · `output/renovation-video.mp4`

## Workflow

1. Localize a imagem do interior finalizado.
2. Analise: tipo de ambiente, posição e altura da câmera, perspectiva, dimensões, paredes,
   janelas, portas e aberturas, pé-direito, piso, mobiliário, embutidos, materiais, direção
   da luz e estilo.
3. Trate a imagem enviada como a referência **depois**; salve-a em `output/completed-interior.png`.
4. Gere a imagem **antes da construção** com **GPT Image**, usando o prompt abaixo, e salve
   em `output/before-construction.png`.
5. **Portão de consistência** — compare as duas: mesma câmera, mesmas paredes, mesmas
   aberturas, mesmo pé-direito. Se o layout mudou, **regenere**; não leve um "antes" errado
   para o vídeo.
6. Gere o vídeo com **Higgsfield Seedance 2.0 Mini** (Higgsfield MCP), com o "antes" como
   `@image1` e o finalizado como `@image2`, usando o prompt de vídeo abaixo.
7. Salve em `output/renovation-video.mp4` e confira com `ffprobe` (dimensão e duração reais,
   não o JSON da resposta).

Atalho: `python3 agnes/rodar.py --img agente --video higgsfield` prepara os arquivos e
escreve os dois handoffs (`output/HANDOFF-imagem.md`, `output/HANDOFF-video.md`) com os
prompts e caminhos já preenchidos.

## Prompt — imagem antes da construção

Create a photorealistic before-construction version of the submitted completed interior.

Preserve exactly: the original camera position, camera height, lens perspective, room
dimensions, ceiling height, wall positions, windows, doors, openings, structural columns,
architectural geometry and natural lighting direction.

Remove: all furniture, decoration, finished flooring, wall finishes, built-in cabinets,
completed lighting fixtures, luxury materials, artwork and accessories.

Transform the room into a clean unfinished construction shell with raw cement or plaster
walls, an unfinished ceiling, bare flooring, empty space and simple natural daylight.

The output must look like the exact same room before renovation began.

Do not change the architecture. Do not change the camera angle. Do not add new doors or
windows. Do not add people. Do not add furniture. Do not add text or logos. Avoid exposed
loose wires and complicated construction machinery.

## Prompt — vídeo Seedance

Create a realistic time-lapse renovation transformation video with a locked camera,
before: `@image1`, after: `@image2`, showing many renovation workers actively moving around
the room wearing yellow safety helmets, orange reflective safety vests, work gloves and
construction boots.

Show fast-paced work such as measuring walls, carrying materials, drilling, plastering,
painting, installing lights, laying flooring, mounting cabinets, moving ladders, cleaning
dust and assembling furniture.

As the time-lapse progresses, the unfinished room gradually transforms into a fully
renovated modern interior, with raw cement walls becoming smooth finished walls, the exposed
ceiling becoming a polished ceiling with lighting, bare floors becoming premium flooring,
and the empty space filling with elegant built-ins and stylish furniture.

Keep the motion busy, realistic, and coordinated, with natural construction activity, dust
movement, and a clear sense of progress throughout.

## Regras de consistência

Travar: ângulo de câmera, perspectiva, dimensões, pé-direito, paredes, janelas, portas,
aberturas, elementos estruturais. Só mudam o estágio da obra e os acabamentos.
