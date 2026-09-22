# task-manager-api

API de Task Manager em Python/Flask, organizada em camadas: as rotas só fazem binding, os controllers traduzem HTTP, os serviços concentram a regra de negócio e os repositórios são o único lugar que monta query.

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env    # opcional; sem ele a app sobe com defaults e avisa no log
python seed.py
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000` por padrão. O `seed.py` cria o schema e popula o SQLite (`instance/tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**, caso contrário os endpoints vão retornar listas vazias.

Sem `SECRET_KEY` no ambiente, o boot gera uma chave efêmera e registra um `WARNING`: as sessões assinadas não sobrevivem ao restart. Sem `CORS_ORIGINS`, todas as origens são liberadas, também com aviso. Defina as duas em produção.

## Estrutura

```
config/         configuração lida do ambiente (único lugar com valor por ambiente)
models/         entidades, serializadores e predicados de domínio
repositories/   acesso a dados — único lugar que monta query
services/       regra de negócio e validação
controllers/    orquestração HTTP: lê a requisição, chama o serviço, monta a resposta
routes/         registro de caminho e método
middlewares/    tratamento central de erro
exceptions.py   erros de domínio, independentes da camada HTTP
app.py          composition root
```

## Paginação

As listagens aceitam `limit` e `offset` opcionais (`GET /tasks?limit=20&offset=40`), com teto de 200 por página. Sem os parâmetros, a resposta traz todos os registros.

## Autenticação

**Não há autenticação.** O `POST /login` valida a senha e devolve um token stub (`fake-jwt-token-<id>`), previsível, não assinado e que nenhuma rota verifica. Toda rota de escrita aceita requisição anônima, e `POST /users` aceita `role` no corpo. Implementar autenticação real é decisão de produto — ver o relatório em `reports/audit-task-manager-api.md`.
