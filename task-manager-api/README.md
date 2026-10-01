# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env      # defina SECRET_KEY
python seed.py            # cria o schema e popula o banco
python app.py             # sobe em http://127.0.0.1:5000
```

O `seed.py` recria os dados de exemplo no SQLite (`instance/tasks.db`). Bancos criados por versões anteriores guardam senhas em MD5 e precisam ser re-semeados. Para só criar o schema sem dados: `flask --app app init-db`.

Configuração por ambiente (ver `.env.example`):

| Variável | Default | Observação |
|---|---|---|
| `SECRET_KEY` | efêmera, com aviso no log | assina os tokens; sem ela, todo token cai a cada restart |
| `DEBUG` | `false` | |
| `HOST` / `PORT` | `127.0.0.1` / `5000` | use `HOST=0.0.0.0` para expor na rede |
| `DATABASE_URL` | `sqlite:///tasks.db` | |
| `CORS_ORIGINS` | `*` | lista separada por vírgula |
| `TOKEN_TTL_HOURS` | `12` | |

## Autenticação

`POST /login` devolve um JWT em `token`. Envie-o como `Authorization: Bearer <token>`.

| Nível | Rotas |
|---|---|
| público | `GET /`, `GET /health`, `POST /login`, `POST /users`, `GET /categories` |
| credencial | `GET /tasks`, `GET /tasks/<id>`, `GET /tasks/search`, `GET /tasks/stats`, `POST /tasks` |
| responsável pela task ou admin | `PUT /tasks/<id>`, `DELETE /tasks/<id>` |
| o próprio usuário ou admin | `GET/PUT/DELETE /users/<id>`, `GET /users/<id>/tasks`, `GET /reports/user/<id>` |
| admin | `GET /users`, `GET /reports/summary`, `POST/PUT/DELETE /categories` |

O cadastro sempre cria usuários com papel `user`. Só admin altera `role` e `active`.

Usuários do seed: `joao@email.com` / `1234` (admin), `maria@email.com` / `abcd`, `pedro@email.com` / `pass`.

Listagens (`/tasks`, `/tasks/search`, `/users`, `/categories`) aceitam `limit` (1–200) e `offset` opcionais; sem eles, devolvem tudo.

## Estrutura

```
app.py           composition root (create_app)
config/          configuração do ambiente e logging
routes/          caminho, método e nível de acesso
controllers/     request → service → response
services/        regra de negócio e emissão de token
repositories/    acesso a dados e unidade de trabalho
models/          entidades, serialização e constantes de domínio
middlewares/     autenticação e tratamento central de erro
```
