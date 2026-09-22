================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python 3.13 + Flask 3.1.1 (flask-cors 5.0.1, sqlite3 stdlib)
Files:   4 analyzed | ~780 lines of code
Date:    2026-09-21

## Summary
CRITICAL: 7 | HIGH: 7 | MEDIUM: 10 | LOW: 6

## Findings

### [CRITICAL] Injeção de SQL por concatenação (AP-01)
**File:** `models.py:28, 48-49, 58-60, 68, 92, 110, 127-128, 140, 149-150, 155, 158-160, 164-165, 174, 188, 192, 220, 224, 280, 289-297` (21 queries; nenhuma usa placeholder)
**Description:** Toda query de `models.py` é montada por concatenação de string com valores vindos de path params, query string e corpo JSON. O caso mais grave é `login_usuario` (`models.py:109-111`), onde email e senha entram crus no `WHERE`, e `buscar_produtos` (`models.py:289-297`), que monta `WHERE 1=1` com `query +=`.
**Impact:** `POST /login` com `{"email": "a' OR '1'='1", "senha": "x' OR '1'='1"}` autentica como o primeiro usuário da tabela; `GET /produtos/busca?q=' UNION SELECT ...` dumpa a tabela `usuarios` com senhas em claro.
**Recommendation:** Trocar todas as 21 queries por parâmetros ligados (`?`) com tupla de argumentos. (→ PB-01)

### [CRITICAL] Endpoint perigoso exposto sem proteção (AP-02)
**File:** `app.py:59-78` (`POST /admin/query`), `app.py:47-57` (`POST /admin/reset-db`)
**Description:** `/admin/query` executa SQL arbitrário recebido no corpo da requisição e devolve o resultado; `/admin/reset-db` apaga as quatro tabelas. Nenhum dos dois verifica identidade.
**Impact:** Qualquer cliente anônimo na rede faz `DROP TABLE usuarios`, lê o hash/senha de todo mundo, ou zera o banco de produção com um único POST.
**Recommendation:** Remover ambos os endpoints. (→ PB-13 — **exceção de contrato declarada**)

### [CRITICAL] Modo debug habilitado em bind público (AP-08)
**File:** `app.py:8` (`app.config["DEBUG"] = True`), `app.py:88` (`app.run(host="0.0.0.0", port=5000, debug=True)`)
**Description:** O servidor sobe com o debugger do Werkzeug ligado e escutando em todas as interfaces de rede.
**Impact:** O console interativo do Werkzeug exposto na rede é execução remota de código arbitrário no host; além disso, todo erro devolve stack trace com trechos do código-fonte.
**Recommendation:** Mover `DEBUG`, host e porta para variáveis de ambiente com default seguro (`DEBUG=False`, `host=127.0.0.1`). (→ PB-02)

### [CRITICAL] Segredo hardcoded (AP-03)
**File:** `app.py:7`
**Description:** `SECRET_KEY` é o literal `"minha-chave-super-secreta-123"`, versionado no repositório.
**Impact:** Quem lê o repositório forja qualquer cookie de sessão assinado pela aplicação; a chave não pode ser rotacionada sem novo deploy.
**Recommendation:** Ler de variável de ambiente, sem default em produção. (→ PB-02)

### [CRITICAL] Dado sensível em resposta HTTP — senha (AP-04)
**File:** `models.py:84` (`get_todos_usuarios`), `models.py:100` (`get_usuario_por_id`)
**Description:** Os dicionários serializados de usuário incluem o campo `senha`, e são devolvidos sem filtro por `GET /usuarios` (`controllers.py:128-134`) e `GET /usuarios/<id>` (`controllers.py:136-144`).
**Impact:** Um `GET /usuarios` anônimo devolve nome, email e senha em texto claro de todos os usuários da base, incluindo o `admin@loja.com`.
**Recommendation:** Remover `senha` do serializer de usuário; o resto do objeto permanece idêntico. (→ PB-14 — **exceção de contrato declarada**)

### [CRITICAL] Dado sensível em resposta HTTP — configuração e chave (AP-04)
**File:** `controllers.py:285-289`
**Description:** `GET /health` devolve `secret_key`, `debug`, `db_path` e `ambiente` no corpo da resposta.
**Impact:** O endpoint público de health-check entrega a `SECRET_KEY` da aplicação e o caminho do arquivo de banco a qualquer cliente — exfiltração sem autenticação.
**Recommendation:** Remover `secret_key`, `debug` e `db_path` da resposta; manter `status`, `database` e `counts`. (→ PB-14 — **exceção de contrato declarada**)

### [CRITICAL] Hash de senha ausente (AP-05)
**File:** `database.py:75-83` (seed), `models.py:105-120` (`login_usuario`), `models.py:122-131` (`criar_usuario`)
**Description:** Senhas são gravadas em texto claro na coluna `usuarios.senha` e a autenticação é uma comparação literal dentro do `WHERE` do SQL.
**Impact:** Qualquer leitura do arquivo `loja.db`, de um backup, ou do `GET /usuarios` entrega todas as credenciais utilizáveis diretamente — sem esforço de quebra.
**Recommendation:** Derivar a senha com `werkzeug.security.generate_password_hash` na escrita e `check_password_hash` na verificação, movendo a comparação do SQL para a aplicação. (→ PB-05)

---

### [HIGH] Regra de negócio na camada errada — controller (AP-09)
**File:** `controllers.py:30-54` (criar produto), `controllers.py:74-90` (atualizar produto), `controllers.py:198-201` (pedido), `controllers.py:242-243` (status de pedido)
**Description:** Validações de domínio (obrigatoriedade, preço/estoque não-negativos, tamanho do nome entre 2 e 200, lista de categorias válidas, lista de status válidos, pedido com ao menos 1 item) vivem dentro dos handlers HTTP.
**Impact:** A regra só é exercitável via requisição HTTP — não há como testá-la unitariamente nem reusá-la, e cada novo canal de entrada precisa reimplementá-la.
**Recommendation:** Extrair para uma camada de serviço/domínio por entidade, deixando o controller apenas traduzindo exceção de domínio em status HTTP. (→ PB-04)

### [HIGH] Regra de negócio na camada errada — repositório (AP-09)
**File:** `models.py:137-146` (total do pedido e checagem de estoque), `models.py:256-262` (faixas de desconto), `models.py:272` (ticket médio)
**Description:** O módulo de acesso a dados calcula o total do pedido, decide se há estoque suficiente e aplica as faixas de desconto sobre o faturamento (10% acima de 10.000, 5% acima de 5.000, 2% acima de 1.000).
**Impact:** A política comercial de desconto só pode ser alterada ou testada com um banco SQLite ao lado; a mesma função mistura política de negócio com montagem de query.
**Recommendation:** Mover o cálculo de total, a verificação de estoque e as faixas de desconto para a camada de serviço; deixar o repositório devolvendo linhas. (→ PB-04)

### [HIGH] God module (AP-06)
**File:** `models.py:1-314`, `controllers.py:1-292`
**Description:** `models.py` concentra acesso a dados e regra de negócio para quatro domínios (produtos, usuários, pedidos, relatórios); `controllers.py` concentra HTTP, regra de negócio, notificações e — em `health_check` — SQL cru.
**Impact:** Qualquer mudança em qualquer um dos quatro domínios toca os mesmos dois arquivos, maximizando conflito de merge e raio de regressão.
**Recommendation:** Quebrar por domínio em repositórios, serviços e controllers separados. (→ PB-03)

### [HIGH] Acesso a dados sem camada própria (AP-13)
**File:** `controllers.py:3` + `controllers.py:266-274`, `app.py:4` + `app.py:49-55`, `app.py:66-76`
**Description:** O módulo de controllers e o entry point importam `get_db` e executam SQL diretamente — `health_check` roda quatro `SELECT`, `reset_database` roda quatro `DELETE`, `executar_query` roda SQL do cliente.
**Impact:** A camada de dados deixa de ser o único ponto de acesso ao banco; trocar de storage exige varrer todos os arquivos, e o controller passa a depender do driver.
**Recommendation:** Toda query atrás de um repositório; controllers só chamam serviço. (→ PB-03)

### [HIGH] Escrita multi-entidade sem transação (AP-10)
**File:** `models.py:133-169`
**Description:** `criar_pedido` insere o pedido, insere N itens e debita o estoque de N produtos com um único `commit()` no fim (`models.py:168`), sem `BEGIN` explícito e sem `rollback()` em nenhum caminho de erro.
**Impact:** Uma exceção no meio do laço (produto removido concorrentemente, erro de disco) deixa escritas pendentes na conexão global compartilhada, que serão confirmadas pelo `commit()` de uma requisição posterior não relacionada — pedido com itens faltando ou estoque debitado sem venda.
**Recommendation:** Envolver a operação inteira em transação explícita com rollback no `except`. (→ PB-07)

### [HIGH] Estado global mutável (AP-11)
**File:** `database.py:4-5` (`db_connection = None`, `db_path = "loja.db"`), `database.py:8-10`
**Description:** A conexão SQLite é um singleton de módulo criado com `check_same_thread=False` e compartilhado por todas as requisições.
**Impact:** Com o servidor servindo requisições concorrentes, dois handlers compartilham cursor e transação: um `commit()` de uma requisição confirma o trabalho parcial de outra, e não há isolamento nem pool.
**Recommendation:** Conexão por requisição (`flask.g` + `teardown_appcontext`), caminho do banco vindo de config. (→ PB-04)

### [HIGH] Efeito colateral escondido no fluxo (AP-12)
**File:** `controllers.py:208-210`, `controllers.py:247-250`
**Description:** O handler de criação de pedido dispara "envio" de email, SMS e push; o handler de atualização de status dispara notificações condicionais de aprovação e cancelamento — tudo via `print`, dentro do controller.
**Impact:** Nada disso é anunciado pelo contrato da rota nem é desligável; quando virar integração real, a falha do provedor de email derruba a criação do pedido, que já foi persistida.
**Recommendation:** Extrair para um serviço de notificação injetado, chamado pela camada de serviço após o commit. (→ PB-04)

---

### [MEDIUM] Queries N+1 (AP-17)
**File:** `models.py:187-193` (`get_pedidos_usuario`), `models.py:219-225` (`get_todos_pedidos`), `models.py:154-160` (`criar_pedido`)
**Description:** Para cada pedido é feita uma query de itens (`cursor2`) e, para cada item, uma query do nome do produto (`cursor3`). `criar_pedido` refaz o `SELECT preco` de cada produto que já havia consultado no laço anterior.
**Impact:** `GET /pedidos` com 100 pedidos de 3 itens dispara 401 queries; o custo cresce linearmente com o volume da tabela e a rota degrada sem aviso.
**Recommendation:** Um `JOIN` entre `pedidos`, `itens_pedido` e `produtos`, agrupando em memória. (→ PB-06)

### [MEDIUM] Tratamento de erro repetido sem handler central (AP-21)
**File:** `controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292` (16 ocorrências), `app.py:77-78`
**Description:** Todo handler repete `except Exception as e: return jsonify({"erro": str(e)}), 500`, devolvendo a mensagem crua da exceção ao cliente. Não existe error handler registrado no Flask.
**Impact:** Detalhe interno vaza na resposta (nome de tabela, SQL malformado, caminho de arquivo) e mudar o formato de erro da API exige editar 17 lugares.
**Recommendation:** Registrar `@app.errorhandler` central com exceções de domínio tipadas; remover os `try/except` dos handlers. (→ PB-08)

### [MEDIUM] Duplicação entre handlers irmãos (AP-20)
**File:** `controllers.py:24-62` vs `controllers.py:64-96`
**Description:** `criar_produto` e `atualizar_produto` repetem o mesmo bloco de extração e validação — e **já divergiram**: a atualização não valida tamanho do nome (`controllers.py:47-50`) nem a lista de categorias válidas (`controllers.py:52-54`).
**Impact:** `PUT /produtos/1` aceita `{"categoria": "qualquer-coisa"}` e nome de 1 caractere, que o `POST` rejeitaria — a regra de categoria é contornável por quem usar a rota certa.
**Recommendation:** Um único validador de payload de produto, compartilhado pelos dois fluxos. (→ PB-12)

### [MEDIUM] Contrato de resposta sem serializer único (AP-22)
**File:** `models.py:12-21, 31-40, 304-313` (produto, 3x), `models.py:79-86, 95-102` (usuário, 2x), `models.py:178-199, 211-231` (pedido, 2x)
**Description:** O dicionário de cada recurso é remontado campo a campo em cada função, sem fonte única de verdade.
**Impact:** Adicionar um campo a produto exige três edições; esquecer uma faz a mesma entidade responder com formatos diferentes dependendo da rota — foi exatamente assim que `senha` acabou em dois serializers de usuário e em nenhum filtro.
**Recommendation:** Um serializer por entidade, usado por todos os repositórios. (→ PB-12)

### [MEDIUM] Schema sem constraints de integridade (AP-23)
**File:** `database.py:14-53`
**Description:** As quatro tabelas são criadas sem `NOT NULL`, sem `UNIQUE` e sem `FOREIGN KEY`: `usuarios.email` aceita duplicatas, `pedidos.usuario_id` e `itens_pedido.produto_id` não referenciam nada.
**Impact:** `POST /usuarios` duas vezes com o mesmo email cria duas contas e torna `login_usuario` ambíguo; deletar um produto deixa itens de pedido apontando para id inexistente.
**Recommendation:** Adicionar `NOT NULL` nos campos obrigatórios, `UNIQUE` em `usuarios.email` e `FOREIGN KEY` em `pedidos.usuario_id`, `itens_pedido.pedido_id` e `itens_pedido.produto_id`. (→ PB-17)

### [MEDIUM] Limpeza em cascata manual (AP-24)
**File:** `models.py:65-70` (`deletar_produto`), `app.py:51-54` (`reset_database`)
**Description:** `deletar_produto` remove a linha de `produtos` sem tocar em `itens_pedido`; o reset apaga as quatro tabelas na ordem certa à mão, porque o banco não garante nada.
**Impact:** Após `DELETE /produtos/1`, `GET /pedidos` passa a devolver `"produto_nome": "Desconhecido"` (`models.py:196`) para pedidos históricos — dado corrompido silenciosamente.
**Recommendation:** `FOREIGN KEY ... ON DELETE` no schema com `PRAGMA foreign_keys = ON`, ou exclusão lógica usando a coluna `ativo` que já existe e nunca é usada. (→ PB-17)

### [MEDIUM] Bootstrap acoplado à inicialização (AP-25)
**File:** `database.py:12-84`
**Description:** `get_db()` cria as quatro tabelas e, se `produtos` estiver vazia, insere 10 produtos e 3 usuários de exemplo — incluindo `admin@loja.com` com senha `admin123`.
**Impact:** Qualquer ambiente que importe o módulo, inclusive produção, ganha um usuário admin com senha conhecida e publicada no repositório; não há versionamento de schema para evoluir as tabelas.
**Recommendation:** Separar DDL e seed em um comando explícito de inicialização, fora do caminho de obtenção de conexão. (→ PB-18)

### [MEDIUM] CORS irrestrito (AP-26)
**File:** `app.py:9`
**Description:** `CORS(app)` habilita `Access-Control-Allow-Origin: *` para todas as rotas, incluindo `/admin/query` e `/usuarios`.
**Impact:** Qualquer site que a vítima visitar consegue chamar a API pelo navegador dela e ler a resposta, inclusive a listagem de usuários com senhas.
**Recommendation:** Restringir `origins` a uma lista vinda de configuração. (→ PB-02)

### [MEDIUM] Dependência uma major atrás (AP-19)
**File:** `requirements.txt:2` (`flask-cors==5.0.1`; corrente: 6.0.5), `requirements.txt:1` (`flask==3.1.1`; corrente: 3.1.3)
**Description:** `flask-cors` está uma versão major atrás da corrente — a linha 5.x é a que acumulou as correções de CORS mal aplicado. Nenhum `DeprecationWarning` foi emitido no boot da aplicação.
**Impact:** A configuração de CORS fica presa ao comportamento antigo de casamento de origem, que é onde os relatos de bypass se concentram.
**Recommendation:** Subir para `flask-cors==6.0.5` e `flask==3.1.3`, revalidando o contrato. (→ PB-11)

### [MEDIUM] Listagens sem ordenação explícita (AP-18)
**File:** `models.py:7`, `models.py:75`, `models.py:174`, `models.py:206`, `models.py:299`
**Description:** Nenhum `SELECT` de listagem tem `ORDER BY`; a ordem do array depende do plano de execução do SQLite.
**Impact:** A ordem é estável hoje por acidente (varredura por rowid), mas muda com a criação de um índice ou uma mudança de plano — quebrando clientes que indexam o array e invalidando qualquer diff de contrato.
**Recommendation:** `ORDER BY id` explícito em todas as listagens. (→ PB-16)

---

### [LOW] Magic numbers e literais repetidos (AP-27)
**File:** `models.py:257-262` (faixas 10000/5000/1000 e multiplicadores 0.1/0.05/0.02), `controllers.py:52` (lista de categorias), `controllers.py:242` (lista de status), `controllers.py:47-50` (limites 2 e 200), `app.py:88` (porta 5000)
**Description:** Valores de domínio cravados no meio da lógica, sem nome.
**Impact:** Mudar uma faixa de desconto exige entender aritmética solta dentro de uma função de repositório; a lista de status válidos não tem fonte única.
**Recommendation:** Constantes nomeadas na camada de domínio. (→ PB-19)

### [LOW] `print` como logging (AP-28)
**File:** `controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208, 209, 210, 219, 248, 250`, `app.py:56, 83-86` (19 ocorrências)
**Description:** Toda a saída de diagnóstico e auditoria — incluindo erros e o log de login bem-sucedido com o email do usuário — sai por `print`, sem nível nem destino configurável.
**Impact:** Não há como baixar a verbosidade em produção nem enviar erro para agregador; os erros vão para stdout misturados com o log de acesso.
**Recommendation:** Módulo `logging` com níveis e handler configurável. (→ PB-20)

### [LOW] Nomes não descritivos (AP-29)
**File:** `models.py:187, 191, 219, 223` (`cursor2`, `cursor3`), `models.py:24, 43, 54, 65, 89` e `controllers.py:14, 64, 98` (parâmetro `id` sombreando o builtin), `controllers.py:10, 21, 60` (`e` para exceção)
**Description:** Cursores numerados e o parâmetro `id` sombreando a função builtin do Python.
**Impact:** `cursor2`/`cursor3` só existem para sustentar o N+1 — o nome esconde o problema em vez de nomeá-lo.
**Recommendation:** Renomear para `produto_id`/`usuario_id` e eliminar os cursores numerados junto com o N+1. (→ PB-19)

### [LOW] Imports mortos (AP-30)
**File:** `models.py:2` (`import sqlite3`), `database.py:2` (`import os`)
**Description:** Nenhum dos dois módulos referencia os símbolos importados — `sqlite3` aparece uma única vez em `models.py`, na própria linha do import.
**Impact:** Sugere ao leitor que `models.py` fala com o driver diretamente, quando não fala.
**Recommendation:** Remover. (→ PB-21)

### [LOW] Ausência de paginação (AP-31)
**File:** `models.py:7` (`/produtos`), `models.py:75` (`/usuarios`), `models.py:206` (`/pedidos`), `models.py:299` (`/produtos/busca`)
**Description:** Todas as listagens fazem `SELECT *` sem `LIMIT` e serializam a tabela inteira.
**Impact:** `GET /pedidos` carrega todos os pedidos da história da loja em memória e ainda dispara o N+1 sobre cada um.
**Recommendation:** `limit`/`offset` com default, expostos como query params opcionais. (→ PB-22)

### [LOW] Verbosidade evitável (AP-32)
**File:** `controllers.py:8, 11, 54, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250`, `models.py:143, 145`
**Description:** Mensagens construídas com `"texto " + str(valor) + " texto"` em vez de f-string, em 19 pontos.
**Impact:** Exatamente o mesmo hábito de concatenação que produziu as 21 injeções de SQL do AP-01 — o estilo normaliza o padrão perigoso.
**Recommendation:** f-strings. (→ PB-19)

## Contract Exceptions

- `app.py:59-78` — endpoint `POST /admin/query` removido (AP-02)
- `app.py:47-57` — endpoint `POST /admin/reset-db` removido (AP-02)
- `models.py:84, 100` — campo `senha` removido do serializer de usuário; afeta o corpo de `GET /usuarios` e `GET /usuarios/<id>`, resto do objeto intacto (AP-04)
- `controllers.py:285-289` — campos `secret_key`, `debug` e `db_path` removidos do corpo de `GET /health`; `status`, `database`, `counts`, `versao` e `ambiente` mantidos (AP-04)

## Requires Product Decision

- **AP-07 — Autenticação ausente ou simulada.** `app.py:11-30`: nenhuma das 19 rotas verifica identidade. `controllers.py:167-186` + `models.py:105-120`: `POST /login` valida a senha e devolve o objeto do usuário, sem emitir token, cookie de sessão ou qualquer credencial verificável — o cliente não recebe nada que possa apresentar na próxima requisição. `controllers.py:146-165`: o cadastro é público.
  **Transformação descrita, não aplicada:** emitir JWT assinado com a `SECRET_KEY` vinda de ambiente no `/login`, e exigir `Authorization: Bearer` num decorator aplicado às rotas de escrita (`POST/PUT/DELETE /produtos`, `PUT /pedidos/<id>/status`, `GET /usuarios`) e às rotas de dado de terceiro (`GET /pedidos`, `GET /pedidos/usuario/<id>`).
  **Por que não foi aplicada:** toda rota protegida passaria a responder 401 para as requisições do baseline, quebrando o contrato HTTP que a Fase 3 se compromete a preservar. Exige decisão de produto sobre quais rotas são públicas e como os clientes existentes migram.

================================
Total: 30 findings
================================
