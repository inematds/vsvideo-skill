# Crie um vídeo de reforma e ambientação virtual com uma única skill do Codex

Vídeos de ambientação virtual são uma maneira poderosa de mostrar como um ambiente inacabado pode se transformar em um espaço totalmente pronto.

Em vez de criar manualmente cada imagem, escrever prompts e mover arquivos entre diferentes ferramentas, podemos controlar todo o fluxo de trabalho utilizando uma única skill do Codex.

Neste tutorial, começamos com um projeto vazio, anexamos uma imagem de design de interiores diretamente no chat do Codex, geramos uma imagem correspondente do ambiente antes da construção e transformamos as duas imagens em um timelapse realista de reforma utilizando o Higgsfield Seedance 2.0 Mini.

Todo o processo é gerenciado por um único arquivo `SKILL.md`.

## Comece com um projeto vazio

O projeto começa com uma pasta vazia. Dentro dela, criamos uma pasta para os arquivos gerados e outra para a skill de ambientação virtual.

```text
virtual-staging-video/
│
├── output/
│
└── skills/
    └── virtual-staging-video/
        └── SKILL.md
```

O arquivo `SKILL.md` contém tudo o que o Codex precisa para concluir o projeto. Isso inclui as instruções do fluxo de trabalho, o prompt do GPT Image, as regras de consistência visual, o prompt de vídeo, o roteamento entre modelos, a lógica de fallback e os locais de saída dos arquivos.

Não é necessário utilizar skills separadas para análise de imagens, biblioteca de prompts ou direção de vídeo. Como este é um fluxo de trabalho pequeno e previsível, uma única skill de orquestração é suficiente.

## O que a skill faz

A skill começa analisando a imagem de design de interiores anexada ao chat do Codex.

Ela identifica a posição da câmera, as dimensões do ambiente, a perspectiva, paredes, janelas, portas, teto, móveis, materiais, iluminação e o estilo do ambiente.

A imagem enviada é tratada como a referência do espaço depois da reforma, já completamente finalizado.

Em seguida, o Codex utiliza o GPT Image 2 para gerar uma versão correspondente do mesmo ambiente antes da construção. O requisito mais importante é a consistência visual.

A imagem gerada deve preservar os mesmos elementos:

- Ângulo de câmera
- Dimensões do ambiente
- Janelas e portas
- Posição das paredes
- Altura do teto
- Perspectiva
- Características estruturais

Somente o estágio da construção deve mudar.

Os móveis, pisos, revestimentos, armários planejados, objetos de decoração, luminárias e acabamentos sofisticados são removidos. O ambiente se transforma em uma estrutura limpa e inacabada, com paredes brutas, piso sem acabamento, teto incompleto e iluminação natural simples.

## Mecanismo de fallback do GPT Image 2

O Codex GPT Image 2 continua sendo o método principal de geração de imagens.

A skill tenta primeiro gerar a imagem anterior à construção diretamente pelo Codex. Caso a função retorne um erro, ultrapasse o tempo limite ou não produza uma imagem utilizável, o Codex realiza uma nova tentativa.

Se a segunda tentativa também falhar, o fluxo muda automaticamente para a opção GPT Image 2 disponível por meio do Higgsfield.

A mesma imagem de referência e o mesmo prompt são utilizados, portanto o resultado desejado não é alterado.

A ordem de execução é:

```text
Codex GPT Image 2
        ↓
Nova tentativa com Codex GPT Image 2
        ↓
Fallback para Higgsfield GPT Image 2
        ↓
Validação da imagem gerada
```

Esse fallback evita que um problema temporário na geração de imagens interrompa todo o projeto.

Antes de executar a demonstração, conecte o plugin do Higgsfield seguindo o guia de conexão disponível no site. Depois de concluir a conexão, abra o aplicativo do ChatGPT e confirme se o Higgsfield está disponível.

## Criação do vídeo de reforma

Quando a imagem anterior à construção estiver pronta, a skill prepara as duas referências:

```text
@image1 = Antes da construção
@image2 = Ambiente finalizado
```

As duas imagens são então enviadas para o Higgsfield Seedance 2.0 Mini.

O prompt de vídeo solicita que o modelo crie um timelapse realista de reforma com a câmera completamente fixa. Os profissionais da construção circulam pelo ambiente utilizando capacetes de segurança, coletes refletivos, luvas e botas de construção.

Eles executam ações como medir paredes, transportar materiais, utilizar furadeiras, aplicar reboco, pintar paredes, instalar iluminação, colocar o piso, montar armários, movimentar escadas, montar móveis e limpar a poeira.

À medida que o timelapse avança, o ambiente inacabado se transforma gradualmente no interior finalizado.

As paredes brutas tornam-se paredes lisas e acabadas. O teto exposto transforma-se em um teto refinado com iluminação instalada. O piso bruto torna-se um revestimento de alto padrão, e o espaço vazio é preenchido com móveis planejados, mobiliário e decoração.

A presença dos trabalhadores torna a transformação mais realista e ajuda a esconder pequenas diferenças entre as imagens de antes e depois.

A câmera deve permanecer fixa durante todo o vídeo, garantindo que a geometria do ambiente permaneça estável.

## Execute todo o processo dentro do Codex

Para a demonstração final, anexe diretamente no chat do Codex a imagem do ambiente já finalizado.

Depois, utilize uma única instrução:

```text
Use a imagem de design de interiores anexada para criar
um vídeo de reforma e ambientação virtual.

Siga a skill virtual-staging-video.

Use o Codex GPT Image 2 como gerador principal de imagens.
Caso ele falhe após uma nova tentativa, utilize a rota
Higgsfield GPT Image 2 como fallback.

Gere o vídeo de reforma utilizando o Higgsfield Seedance 2.0 Mini
e salve todos os arquivos gerados dentro do projeto.
```

O Codex lê a skill, analisa a imagem anexada, gera a versão anterior à construção, valida o par de imagens, prepara o prompt para o Seedance, gera o vídeo da reforma e salva os resultados.

O projeto final contém:

```text
output/
├── before-construction.png
├── completed-interior.png
├── renovation-video.mp4
└── generation-log.json
```

O resultado é um vídeo completo de reforma e ambientação virtual, criado a partir de uma imagem de ambiente interno, uma instrução enviada ao Codex e um único arquivo de skill.

Esse fluxo de trabalho pode ser utilizado em marketing imobiliário, divulgação de imóveis na planta, prévias de reformas, apresentações de design de interiores e conteúdos imobiliários para redes sociais.

## Recursos

Skill de ambientação virtual
