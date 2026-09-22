# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

Refatorada de monolito para MVC. O contrato HTTP é idêntico ao da versão original —
as três rotas respondem os mesmos status, corpos e content-types.

## Como rodar

```bash
npm install
npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e o seed
roda no boot fora de produção. Exemplos de requisições estão em `api.http`.

Para subir em outra porta: `PORT=3999 npm start`.

## Configuração

Copie `.env.example` para `.env`. Todas as variáveis têm default exceto
`PAYMENT_GATEWAY_KEY` — sem ela a autorização de pagamento roda em modo stub e
avisa no boot. Node 22 lê o arquivo com `node --env-file=.env src/app.js`.

## Estrutura

```
src/
├── config/        # ambiente, logger e conexão — únicos pontos que leem process.env
├── database/      # schema (DDL) e seed, acionados explicitamente pelo entry point
├── models/        # acesso a dados, um por entidade; não conhecem HTTP
├── services/      # regra de negócio que atravessa entidades
├── controllers/   # validam entrada, chamam a regra, montam a resposta
├── routes/        # caminho + método + binding; camada mais fina
├── middlewares/   # erro centralizado e wrapper de handler async
├── errors/        # AppError
├── create-app.js  # grafo de dependências
└── app.js         # entry point
```

## O que não foi corrigido

Duas decisões ficaram de fora por dependerem de produto, e estão descritas no
relatório de auditoria em `reports/audit-ecommerce-api-legacy.md`:

- **Autenticação** — nenhuma rota verifica identidade. Adicioná-la faria as três
  responderem 401 e quebraria o contrato preservado aqui.
- **Integridade referencial** — as `FOREIGN KEY` estão declaradas em
  `src/database/schema.js`, mas o `PRAGMA foreign_keys` continua desligado.
  Ligá-lo mudaria o relatório financeiro depois de um `DELETE /api/users/:id`.
