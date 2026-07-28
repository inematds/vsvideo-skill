# Plano — trocar Higgsfield/GPT Image por Agnes AI

Objetivo: rodar a skill `virtual-staging-video` inteiramente na **API Agnes AI**
(`apihub.agnes-ai.com`, custo US$ 0), sem MCP do Higgsfield e sem GPT Image.

Fonte dos fatos de API: `~/projetos/agnes-nei/NOTAS-API.md` (medições reais) e as skills
`imagens-agnes` / `videos-agnes`.

## 1. O que muda

| Etapa | Hoje | Com Agnes |
|---|---|---|
| Imagem "antes da obra" | GPT Image | `POST /v1/images/generations`, modelo `agnes-image-2.1-flash`, **img2img** com a foto do interior em `extra_body.image` |
| Vídeo antes→depois | Higgsfield Seedance 2.0 Mini (MCP) | `POST /v1/videos`, modelo `agnes-video-v2.0`, `extra_body.mode="keyframes"` com o par A→B |
| Transporte | ferramentas MCP | HTTP direto (chave em `~/projetos/agnes-nei/.env`) |

O `mode:"keyframes"` do Agnes é **exatamente** o que a skill precisa: ele interpola entre
duas imagens dadas — o mesmo papel de `@image1`/`@image2` no Seedance.

Ponto a favor, medido: o modelo de imagem do Agnes é **forte em ambiente e fraco em
personagem** (NOTAS-API §6). Interior sem gente é o caso bom dele. O ponto fraco aparece no
vídeo, onde o prompt pede operários — ver risco R3.

## 2. Restrições da API que o pipeline precisa respeitar

Todas medidas, não supostas:

- **Prompt em inglês.** Em PT o filtro devolve HTTP 400 determinístico. Os prompts do
  `SKILL.md` já estão em inglês — manter.
- **img2img ignora `ratio`.** Usar `size:"1312x736"` explícito, **sem** `ratio`; senão volta
  1024×1024.
- **Máx. 10 MB por imagem** de referência → redimensionar a foto do usuário antes de enviar.
- **Máx. 2 referências úteis** (5 destroem a imagem). Aqui usamos 1 — sem problema.
- **Sem `seed` no modelo de imagem** (existe no de vídeo) → o "antes" não é reproduzível;
  regenerar é a única correção.
- **Vídeo:** `num_frames ≤ 441` (18,4 s @24 fps), regra **8n+1**; `frame_rate` 1–60.
- **Rate limit real de vídeo: 5 req/min** → HTTP 429. Throttle obrigatório.
- **~34 % de HTTP 503** na geração de imagem → retry com backoff (100 % recuperado no retry
  na amostra do NOTAS).
- **Keyframes aceitam data URI base64** (a doc diz que exige URL pública — é mentira,
  testado com payload de 3,2 MB). Ou seja: **não precisamos hospedar nada**.
- **O JSON mente sobre o tamanho.** Pediu 1312×736, o MP4 saiu 1280×704 (razão 1.82, não
  1.78). Sempre conferir com `ffprobe` e, se necessário, corrigir no ffmpeg.
- Vídeo é **assíncrono**: `POST /v1/videos` devolve id → `GET /agnesapi?video_id=<ID>` até
  `completed`/`failed`. Tempo observado: 19–50 s por clipe de ~3,4 s.

## 3. Implementação

Em vez de deixar a skill "conversar" com HTTP na mão a cada rodada, criar **um script
determinístico** no repo e a skill passa a chamá-lo. Isso torna o retry, o throttle e a
checagem de tamanho reprodutíveis.

```
vsvideo-skill/
├── agnes/
│   ├── client.py       # POST imagens + POST/poll vídeo, retry 503, throttle 429
│   ├── antes.py        # img2img: interior finalizado -> before-construction.png
│   ├── video.py        # keyframes A->B -> renovation-video.mp4
│   └── rodar.py        # orquestra as duas etapas + ffprobe no final
└── skills/virtual-staging-video/SKILL.md   # passa a chamar `python3 agnes/rodar.py`
```

Passos:

1. **`client.py`** — chave lida de `~/projetos/agnes-nei/.env` em runtime (nunca copiada pro
   repo, nunca impressa). Uma função para imagem, uma para vídeo (POST + polling). Retry
   com backoff no 503; espera respeitando o teto de 5 req/min no vídeo. Sempre logar o
   **erro cru** da API — no NOTAS, a mensagem crua sempre estava certa e a conclusão
   automática do script sempre errada.
2. **`antes.py`** — redimensiona `input/interior-design.png` para caber em 10 MB /
   1312×736, chama img2img com o prompt "before-construction" que já existe no `SKILL.md`,
   grava `output/before-construction.png`. Copia a original para
   `output/completed-interior.png`.
3. **Portão de consistência (mantém-se, e fica mais importante).** Sem `seed`, a variação
   entre rodadas é maior que com GPT Image. O agente compara as duas imagens (mesma câmera,
   paredes, aberturas, pé-direito) e **regenera** em vez de seguir. Regra atual do
   `SKILL.md` continua valendo.
4. **`video.py`** — monta as duas imagens como data URI base64, `mode:"keyframes"`,
   `num_frames=145` (6,04 s @24 fps; respeita 8n+1) como default, `seed` fixo para poder
   repetir a mesma rodada, prompt de time-lapse já existente. Faz o polling e baixa o MP4.
5. **Pós-render** — `ffprobe` para conferir dimensão/duração reais; se vier 1280×704,
   corrigir para 16:9 com `ffmpeg -vf "scale=1280:720:flags=lanczos"` (ou crop, decidir no
   teste).
6. **Atualizar `SKILL.md`**: trocar "GPT Image" e "Higgsfield Seedance 2.0 Mini (MCP)" por
   Agnes, trocar o pré-requisito de MCP por `AGNES_API_KEY` + `ffmpeg`, e apontar o comando
   `python3 agnes/rodar.py`. Manter intactos os prompts e as regras de consistência — eles
   não dependem do fornecedor.
7. **Atualizar README e `guia/index.html`** (seção Pré-requisitos e o card do fluxo).

## 4. Teste (o que decide se o plano vale)

Rodar com **uma** imagem real de interior e checar, nesta ordem:

1. O "antes" saiu com a **mesma câmera e a mesma arquitetura**? (o risco principal — ver R1)
2. O MP4 saiu? Duração e dimensão reais batem no `ffprobe`?
3. O time-lapse **transforma de verdade** de A para B, ou só faz um crossfade?

Só depois de 1–3 passarem numa imagem é que vale rodar em três interiores diferentes
(um cômodo social, um quarto, uma cozinha) para medir a taxa de acerto.

## 5. Riscos (e o que fazer com cada um)

- **R1 — o img2img do Agnes reinterpreta em vez de editar.** Ele "preserva estilo e
  composição", mas não é um editor: a arquitetura pode escorregar. Se escorregar, testar
  `/v1/images/edits` (endpoint **existe**, mas o payload correto está em aberto no NOTAS) e,
  se também falhar, manter GPT Image só nesta etapa e usar Agnes só no vídeo. **Essa
  divisão é uma saída legítima, não um fracasso do plano.**
- **R2 — sem `seed` na imagem**, cada regeneração é uma aposta nova. Custa tempo, não
  dinheiro (US$ 0).
- **R3 — o modelo é fraco em personagem** e o prompt do vídeo pede *muitos operários com
  capacete e colete*. Alta chance de figuras deformadas. Mitigação: reescrever o prompt de
  vídeo para privilegiar a **transformação do ambiente** (paredes, piso, luz, mobília
  aparecendo) e deixar os trabalhadores em segundo plano, borrados pelo movimento — o que,
  aliás, é o visual típico de time-lapse de obra.
- **R4 — 18,4 s de teto** por clipe. Suficiente para o produto atual (5–8 s). Se um dia
  quisermos mais, é concatenar clipes.
- **R5 — dados podem treinar o modelo** no plano free (NOTAS §, opt-out não localizado).
  Relevante se a imagem do cliente for confidencial — precisa estar no README, não escondido.

## 6. Ordem de execução

1. `client.py` + `antes.py`, e rodar **só a imagem** numa foto real → decide R1.
2. Se R1 passar: `video.py` + polling + `ffprobe`.
3. Ajustar o prompt de vídeo conforme R3.
4. `rodar.py` amarrando tudo; atualizar `SKILL.md`, README e guia.
5. Commit + push; republicar o guia (Pages já está no ar via Actions).

O passo 1 é o portão: se a imagem "antes" não segurar a arquitetura, o resto do plano muda
(fallback do R1) antes de gastar trabalho no vídeo.
