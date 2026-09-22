# Baseline e diff de contrato

Usado na **Fase 3**. É o que transforma "não quebrei nada" em evidência.

Princípio: capture o comportamento observável **antes** de tocar em qualquer arquivo, refatore, recapture e compare. Sem baseline, a Fase 3 não roda.

---

## 1. Preparar o ambiente

Instale as dependências do projeto em ambiente isolado (`.venv`, `node_modules`) se ainda não existirem. Isso não é modificação do projeto — não conta para o gate.

### Conflito de porta

A porta padrão da aplicação frequentemente está ocupada. Na prática: **5000 é usada pelo AirPlay Receiver no macOS** e 3000 por qualquer app de desenvolvimento.

Verifique antes: `lsof -nP -iTCP:<porta> -sTCP:LISTEN`

Se estiver ocupada, suba em porta alternativa **sem editar o código original** — editar antes da captura contamina o baseline.

| Situação | Estratégia |
|---|---|
| Porta lida de variável de ambiente | `PORT=5055 <comando>` |
| Flask com `app.run()` em `__main__` | `flask --app <modulo> run --port 5055` — ignora o bloco `__main__` e usa o objeto `app` do módulo |
| Express com porta em objeto de config | pré-carregar o módulo de config, mutar, e só então carregar a app — o cache de `require` garante a mesma instância:<br>`node -e "const u=require('./src/utils'); u.config.port=3055; require('./src/app');"` |
| Nenhuma funciona | aborte e peça ao humano para liberar a porta |

Use **a mesma porta** nas duas capturas.

---

## 2. Resetar o estado

As duas capturas precisam partir do mesmo estado de banco, ou todo diff é ruído.

| Padrão do projeto | Reset |
|---|---|
| Arquivo SQLite com seed na primeira conexão | apagar o arquivo `.db` |
| Banco em memória, seed no boot | reiniciar o processo |
| Script de seed separado | apagar o `.db` e rodar o script |
| Banco externo | truncar e re-semear, ou usar schema dedicado |

Procure o `.db` em toda a árvore — alguns frameworks escrevem em subpasta (`instance/` no Flask-SQLAlchemy), não na raiz.

---

## 3. Montar a lista de requisições

Da enumeração de rotas da Fase 1, mais os payloads de qualquer arquivo de exemplos (`*.http`, `*.rest`, Postman, `curl` no README).

Para cada rota: método, caminho, corpo quando houver, e um caso de erro quando for barato (id inexistente, payload inválido). O caso de erro é o que pega regressão em tratamento de exceção.

### Ordem de disparo

Rotas mutantes alteram o que as seguintes leem. Ordem fixa:

1. **leitura** — `GET` de listagens e detalhes;
2. **criação** — `POST`;
3. **leitura pós-criação** — os mesmos `GET`, para capturar o efeito;
4. **atualização** — `PUT`/`PATCH`;
5. **remoção** — `DELETE`;
6. **destrutivos globais** — reset de banco, se existirem, por último.

A mesma ordem nas duas capturas, sempre.

---

## 4. Gravar

`.refactor-arch/baseline.json`:

```json
{
  "capturedAt": "2026-09-21T18:00:00Z",
  "baseUrl": "http://127.0.0.1:5055",
  "volatileFields": ["created_at", "updated_at", "generated_at", "timestamp", "capturedAt"],
  "sortArraysBy": { "/api/admin/financial-report": "course", "/tasks": "id" },
  "requests": [
    {
      "id": "01-get-produtos",
      "method": "GET",
      "path": "/produtos",
      "status": 200,
      "body": { "sucesso": true, "dados": [ { "id": 1, "nome": "Notebook Gamer" } ] }
    }
  ]
}
```

`.refactor-arch/` entra no `.gitignore` — é artefato de validação, não entrega.

---

## 5. Normalização

**Só normalize o que for comprovadamente volátil.** Cada campo normalizado é uma regressão que o diff deixa de pegar.

| O que | Por quê | Como |
|---|---|---|
| Timestamps gerados no servidor | mudam a cada execução | substituir por `<TIMESTAMP>` |
| Ids auto-increment | podem variar se a ordem de inserção mudar | comparar a forma, não o valor, **só** quando o baseline mostrar variação real |
| Ordem de array não-determinística | ver abaixo | ordenar por chave estável antes de comparar |

### Não-determinismo

Alguns endpoints devolvem a mesma informação em ordem variável — típico de array montado por `push` dentro de callbacks concorrentes (AP-18).

**Detecte antes de capturar:** chame cada endpoint de listagem 5 vezes na aplicação original e compare. Se a ordem variar, registre a chave de ordenação em `sortArraysBy` e ordene os dois lados antes de comparar.

Sem isso, o diff acusa falha onde não houve regressão — e a skill acaba "corrigindo" um problema que não existe.

---

## 6. Comparar

Para cada requisição: status code exato; corpo comparado após normalização, campo a campo.

```
GET  /produtos            200  identico
GET  /produtos/1          200  identico
POST /produtos            201  identico
GET  /usuarios            200  DIFF (esperado)
     - campo removido: dados[].senha        → exceção declarada AP-04
GET  /relatorios/vendas   200  DIFF
     - faturamento_liquido: 8991.0
     + faturamento_liquido: 8991.00
```

## 7. Classificar as divergências

| Tipo | Ação |
|---|---|
| **Exceção declarada** — bate com o que o relatório da Fase 2 listou antes do gate | esperada, segue |
| **Regressão** — mudança não prevista | falha: corrija e recapture |
| **Conserto de bug** — o baseline capturou comportamento errado que a refatoração corrigiu | **apresente ao humano com os dois valores e espere decisão.** Nunca silencie e nunca reverta sozinho |

O terceiro caso é frequente e é sinal de bom trabalho: unificar validação duplicada faz um handler que estourava 500 passar a devolver 400 como o irmão. É melhoria — mas quem decide se entra agora é o humano, não a skill.

---

## 8. Quando abortar

- A aplicação original não sobe → sem baseline, sem Fase 3. Relate o erro de boot como finding.
- Nenhuma porta disponível → peça ao humano para liberar.
- O estado não pode ser resetado de forma reprodutível → relate; o diff não teria valor.

Em todos os casos: **relate e pare.** Refatorar sem poder validar é pior que não refatorar.
