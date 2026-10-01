# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`, já refatorada para MVC.
Auditoria: [`reports/audit-project-1.md`](../reports/audit-project-1.md).

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env      # opcional; preencha SECRET_KEY fora de desenvolvimento
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000` (`HOST`/`PORT` mudam isso; no macOS a 5000 costuma estar ocupada pelo AirPlay Receiver — use `PORT=5055`).
Com `SEED_ON_BOOT=true` (padrão), o banco SQLite (`loja.db`) é criado no primeiro boot com produtos e usuários de exemplo.

Sem `SECRET_KEY`, a aplicação gera uma chave efêmera e avisa no log: os tokens deixam de valer a cada restart.

## Autenticação

`POST /login` devolve um `token` (JWT, 12h). Envie-o como `Authorization: Bearer <token>`.

| Nível | Rotas |
|---|---|
| público | `GET /`, `GET /health`, `GET /produtos`, `GET /produtos/busca`, `GET /produtos/<id>`, `POST /usuarios`, `POST /login` |
| dono ou admin | `GET /usuarios/<id>`, `GET /pedidos/usuario/<id>`, `POST /pedidos` (o `usuario_id` do corpo tem de ser o do token) |
| admin | `POST/PUT/DELETE /produtos`, `GET /usuarios`, `GET /pedidos`, `PUT /pedidos/<id>/status`, `GET /relatorios/vendas` |

Contas de exemplo do seed: `admin@loja.com` / `admin123` (admin), `joao@email.com` / `123456`, `maria@email.com` / `senha123`.

As listagens aceitam `limit` e `offset` opcionais; sem eles, devolvem tudo.

## Estrutura

```
app.py                  composition root
src/config/             settings a partir do ambiente, logging
src/database/           conexão por requisição, schema, seed, paginação
src/models/             acesso a dados por domínio, serializers, constantes
src/services/           regras: produto, usuário/login, pedido, relatório, token, notificação (stub)
src/controllers/        HTTP: lê a requisição, chama o service, monta a resposta
src/views/              Blueprints por domínio, com o nível de acesso de cada rota
src/middlewares/        autenticação/autorização e tratamento central de erro
src/errors.py           erros de domínio mapeados para status HTTP
```
