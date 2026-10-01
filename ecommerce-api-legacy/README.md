# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

Requer Node.js 22.9+.

```bash
npm install
cp .env.example .env   # opcional; preencha JWT_SECRET, ADMIN_EMAIL e ADMIN_PASSWORD
npm start
```

A aplicação sobe em `http://localhost:3000` (`PORT`). O banco SQLite é em memória por padrão (`DB_PATH`) e carrega os dados de exemplo no boot (`SEED_ON_BOOT=false` desliga).

Sem `JWT_SECRET`, um segredo efêmero é gerado no boot e os tokens deixam de valer a cada restart. Sem `ADMIN_EMAIL` e `ADMIN_PASSWORD`, nenhuma conta admin é criada e o relatório financeiro responde 403 a todos. Os avisos aparecem no log de inicialização.

## Autenticação

`POST /api/login` com `{ "eml", "pwd" }` devolve `{ "token" }`, enviado como `Authorization: Bearer <token>`.

| Rota | Acesso |
|---|---|
| `POST /api/checkout` | público — é o checkout que cria a conta do aluno |
| `POST /api/login` | público |
| `GET /api/admin/financial-report` | admin |
| `DELETE /api/users/:id` | o próprio usuário ou admin |

Conta criada no checkout sem `pwd` não tem senha utilizável e não consegue fazer login.

## Pagamento

A autorização de pagamento é um **stub**: cartões que começam com `4` são aprovados sem cobrança alguma. A integração com um gateway real ainda não existe.

## Estrutura

```
src/
├── app.js            # sobe o servidor
├── create-app.js     # composition root: monta dependências, rotas e middlewares
├── config/           # ambiente, logger, conexão
├── database/         # schema, seed de exemplo, provisionamento do admin
├── models/           # acesso a dados, um módulo por tabela
├── services/         # regras: checkout, relatório, usuário, auth, senha, token, gateway
├── controllers/      # validação de entrada e resposta HTTP
├── routes/           # registro de rotas e nível de acesso
├── middlewares/      # autenticação/autorização e erro central
└── errors/           # AppError
```

Exemplos de requisições estão em `api.http`.
