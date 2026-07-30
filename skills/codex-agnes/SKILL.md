---
name: codex-agnes
description: Cria vídeo realista de reforma de aproximadamente 18 segundos a partir de uma foto de interior pronto, usando o Imagegen integrado à assinatura Codex para três keyframes intermediários e a Agnes AI para três segmentos de vídeo. Use quando pedirem “Codex + Agnes”, “imagem pelo Codex e vídeo pela Agnes”, `/vsvideo 18 codex`, ou quando quiserem aprovação dos keyframes antes dos vídeos. Para Agnes em todas as etapas use agnes; para Kling use kling; para GPT Image + Higgsfield use higgsfield.
---

# Virtual staging — Codex Image + Agnes

Usar `rodar.py` para o fluxo automatizado integrado a um agente de filas.

## Fluxo

1. Normalizar a referência final para `1312x736`.
2. Gerar keyframes de trás para frente com `$imagegen`:
   final → acabamento → obra intermediária → obra bruta.
3. Manter a referência final como âncora de câmera e arquitetura.
4. Tentar cada keyframe até três vezes; se nenhum atingir o mínimo, usar o
   melhor e registrar aviso.
5. No modo `preview`, gerar a folha comparativa e parar.
6. No modo `auto18`, criar três vídeos Agnes de 145 frames a 24 fps e
   concatená-los.

Os keyframes não devem conter pessoas. Cada segmento de vídeo deve conter
exatamente dois trabalhadores, limitados a áreas caminháveis e ações
fisicamente possíveis.

## Execução

```bash
python3 skills/codex-agnes/rodar.py \
  --skill-dir skills/agnes \
  --output-dir output/codex-agnes \
  --codex-binary codex \
  --mode preview \
  --image input/interior-design.png
```

Trocar `preview` por `auto18` para seguir diretamente até o MP4.

## Requisitos

- Codex CLI autenticado com ChatGPT pelo mesmo usuário do processo.
- Skill irmã `agnes` disponível ao lado desta pasta.
- `AGNES_API_KEY` no ambiente para os vídeos.
- `ffmpeg` e `ffprobe` no `PATH`.

Não usar `OPENAI_API_KEY`: a imagem integrada conta nos limites da assinatura
Codex. Nunca expor credenciais nos prompts, logs ou artefatos.
