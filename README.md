# photo3x4

Aplicação 100% local para gerar fotos 3x4 brasileiras a partir de uma selfie. O fundo é removido pelo `rembg` em CPU, e a composição final é feita com Pillow. Nenhuma imagem sai do dispositivo/servidor local.

O código da aplicação fica diretamente em `src/`, sem uma subpasta de pacote adicional.

## Versão online

A aplicação está disponível em [photo3x4.heetoo.dev](https://photo3x4.heetoo.dev).

## Instalação

Instale o [uv](https://docs.astral.sh/uv/) e sincronize o ambiente:

```bash
uv sync
```

Na primeira execução, o `rembg` baixa uma vez o modelo CPU leve `u2netp` (cerca de 4 MB); depois o processamento funciona offline. Nenhuma imagem é enviada para fora da máquina.

## Servidor web

```bash
uv run uvicorn src.api:app --reload
```

Abra `http://127.0.0.1:8000`. Para usar no celular conectado à mesma rede Wi-Fi:

```bash
uv run uvicorn src.api:app --host 0.0.0.0 --port 8000
```

Depois acesse `http://IP-DO-COMPUTADOR:8000` no Safari ou Chrome. A câmera do navegador exige contexto seguro em muitos celulares; `localhost` é tratado como seguro, enquanto acesso por IP pode exigir HTTPS conforme o navegador.

## PWA

A interface inclui manifest, ícone e service worker para instalação como aplicativo no navegador. Em `localhost` ela pode ser instalada diretamente; em outros dispositivos, use HTTPS. O shell da interface é mantido em cache, enquanto o processamento de imagens continua sendo feito pelo servidor local.

## Makefile

Atalhos disponíveis:

```bash
make install
make run
make cli ARGS="selfie.jpg --sheet"
```

## Docker

Para executar com Docker Compose:

```bash
cp .env.example .env
docker compose up -d --build
```

O Compose segue as convenções do `home-server-infra`: sobe somente o container da aplicação e conecta-o à rede Docker externa `backend`. Ele não publica portas diretamente no host; o acesso deve ser feito pelo proxy ou túnel configurado na infraestrutura.

Para desenvolvimento local sem a infraestrutura, use `make run` ou `uv run uvicorn src.api:app --reload`.

O modelo CPU `u2netp` é baixado durante o `docker build` e fica embutido na imagem; depois do build, o container não precisa baixar modelos para iniciar ou processar imagens.

O hash do commit é injetado automaticamente nos assets do frontend para evitar cache antigo. Para construir localmente com a revisão atual:

```bash
make build
```

Em um deploy manual, use o mesmo padrão:

```bash
APP_GIT_SHA=$(git rev-parse --short HEAD) docker compose up -d --build
```

O primeiro build precisa de acesso à internet para baixar as dependências e o modelo. Depois, a imagem construída pode ser executada offline.

Para executar em segundo plano:

```bash
docker compose up --build -d
```

Para parar:

```bash
docker compose down
```

Ao acessar pelo celular usando o IP do computador, a câmera pode exigir HTTPS. Nesse caso, configure um proxy local com certificado ou use uma origem segura compatível com o navegador.

## Monitoramento de erros (opcional)

O servidor web integra o [Sentry](https://sentry.io), mas ele só liga quando a variável `SENTRY_DSN` está definida. Sem ela, nada é enviado para fora. A versão online usa o Sentry para registrar erros e uma amostra pequena de requisições. As fotos nunca são anexadas aos eventos (`max_request_body_size="never"`) e dados pessoais não são coletados (`send_default_pii=False`).

| Variável | Padrão | Uso |
| --- | --- | --- |
| `SENTRY_DSN` | vazia | Liga o Sentry |
| `SENTRY_ENVIRONMENT` | `production` | Ambiente dos eventos |
| `SENTRY_TRACES_SAMPLE_RATE` | `0.05` | Fração de requisições com trace (health check e estáticos ficam de fora) |

O `release` dos eventos usa o mesmo `APP_GIT_SHA` dos assets.

## CLI

```bash
uv run photo3x4 selfie.jpg
uv run photo3x4 selfie.jpg --output documento.jpg --size 600x800 --dpi 300
uv run photo3x4 selfie.jpg --sheet
uv run photo3x4 selfie.jpg --transparent
```

As opções `--output`, `--sheet`, `--size`, `--dpi` e `--transparent` estão disponíveis. Sem `--size`, a CLI usa a maior resolução 3:4 possível dentro da imagem original. A CLI reutiliza o mesmo pipeline de remoção de fundo e enquadramento da API.

## API

- `GET /health` — health check.
- `POST /api/process` — recebe o campo multipart `file`, remove o fundo e devolve a captura completa em JPEG para edição.
- `POST /api/sheet` — recebe um JPEG 3x4 no campo `file` e devolve folha 10×15 com 8 cópias.

## Estrutura

O backend fica diretamente em `src`, com rotas em `api.py`, processamento em `processor.py`, composição em `layout.py` e comandos em `cli.py`. O frontend fica em `src/templates` e `src/static`, sendo servido pelo FastAPI com HTML, CSS e JavaScript nativos.

## License

[MIT](LICENSE)
