# vsvideo-skill — Virtual Staging Video

## 📖 Guia de uso

Guia completo (landing + passo a passo): **https://inematds.github.io/vsvideo-skill/guia/**

---

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

> usa a skill virtual-staging-video na imagem em input/interior-design.png

Se a skill estiver instalada em `~/.claude/skills/`, ela também responde como slash command:

```
/virtual-staging-video
```

Antes de rodar, confira o MCP do Higgsfield com `/mcp` — sem ele a skill para nas duas imagens.

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
