# vsvideo-skill — Virtual Staging Video

Skill que transforma **uma foto/render de interior finalizado** num **vídeo time-lapse de reforma** (antes → depois), sem edição manual.

## Como funciona

1. Analisa a imagem enviada (câmera, perspectiva, arquitetura, materiais, luz, estilo).
2. Gera com **GPT Image** a versão **antes da construção** do mesmo ambiente — mesma câmera, mesma arquitetura, só o acabamento muda.
3. Valida a consistência (ângulo/layout). Se divergir, regenera.
4. Gera o **vídeo de reforma** com **Higgsfield Seedance 2.0 Mini** (via Higgsfield MCP), usando a imagem "antes" como `@image1` e a finalizada como `@image2`.

## Estrutura

```text
vsvideo-skill/
├── input/                       # coloque aqui a imagem do interior
│   └── interior-design.png
├── output/                      # gerados
│   ├── before-construction.png
│   ├── completed-interior.png
│   └── renovation-video.mp4
├── skills/
│   └── virtual-staging-video/
│       └── SKILL.md             # a skill
└── doc/                         # tutorial (PT/EN) + spec original
```

## Instalação

Copie a pasta da skill para o diretório de skills do seu agente:

```bash
cp -r skills/virtual-staging-video ~/.claude/skills/
```

Ou trabalhe direto dentro deste repo — o agente encontra a skill em `skills/`.

## Uso

Coloque a imagem em `input/interior-design.png` (ou anexe no chat) e peça:

> "faz o vídeo de reforma dessa imagem"

Gatilhos: *vídeo de reforma*, *virtual staging*, *antes e depois do ambiente*, *time-lapse de obra*.

Saídas em `output/`.

## Pré-requisitos

- Acesso a **GPT Image** (geração da imagem "antes").
- **Higgsfield MCP** configurado, com Seedance 2.0 Mini disponível.

Sem o Higgsfield MCP a skill para após as imagens e avisa — não troca de gerador por conta própria.

## Documentação

- `doc/SKILL.md` — especificação original (prompts completos).
- `doc/virtual_staging_renovation_video_pt.md` — tutorial em português.
- `doc/virtual_staging_renovation_video_en.md` — tutorial em inglês.

---

INEMA · [inema.club](https://inema.club)
