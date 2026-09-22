# code-smells-project

API de E-commerce em Python/Flask, refatorada para MVC pelo desafio `refactor-arch`.

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env    # ajuste os valores
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000`. O schema é criado no boot e, com
`SEED_ON_BOOT=true`, a base recebe produtos e usuários de exemplo.

## Configuração

Tudo que varia por ambiente vem de variável de ambiente — ver `.env.example`.
Sem `SECRET_KEY` definida, a aplicação gera uma chave efêmera a cada boot, o que
invalida sessões entre reinícios mas evita rodar com chave conhecida.

`DEBUG` e `CORS_ORIGINS` são restritivos por padrão: debug desligado e nenhuma
origem cross-site liberada.

## Estrutura

```
app.py                  composition root — só compõe, não define rota nem lógica
src/
├── config/             configuração a partir do ambiente e logging
├── database/           conexão por requisição, DDL e seed (comandos explícitos)
├── models/             acesso a dados por domínio + serializers e constantes
├── services/           regra de negócio e efeitos externos
├── controllers/        handlers HTTP — traduzem request em chamada de serviço
├── views/              blueprints, um por domínio
└── middlewares/        tratamento de erro centralizado
```

## Paginação

As listagens aceitam `limit` e `offset` opcionais (`GET /produtos?limit=20&offset=40`).
Sem `limit`, a listagem é integral — o comportamento anterior é o default.

## Endpoints removidos

`POST /admin/query` e `POST /admin/reset-db` foram removidos: executor de SQL
arbitrário e reset de banco sem autenticação não têm versão segura.
