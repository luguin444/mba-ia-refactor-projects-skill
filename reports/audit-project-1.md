================================
ARCHITECTURE AUDIT REPORT
================================
Project:      code-smells-project
Stack:        Python 3.13.13 + Flask 3.1.1 (flask==3.1.1; Werkzeug 3.1.9)
Dependencies: flask-cors==5.0.1, sqlite3 (stdlib)
Domain:       E-commerce — catálogo de produtos, usuários/login, pedidos com baixa de estoque, relatório de vendas
Architecture: Monolítica — 4 arquivos soltos na raiz sem fronteira de camada; models.py junta query + regra (desconto, estoque), controllers.py junta HTTP + validação + notificação + SQL (health), app.py junta rotas + SQL bruto (admin)
Files:        4 analyzed | ~780 lines of code
Routes:       19 endpoints
DB tables:    produtos, usuarios, pedidos, itens_pedido
Date:         2026-09-30

## Summary
CRITICAL: 9 | HIGH: 7 | MEDIUM: 8 | LOW: 6

## Findings

### [CRITICAL] Injeção de SQL por concatenação (AP-01)
**File:** `models.py:28, 48-49, 58-60, 68, 92, 110, 127-128, 140, 149-150, 280, 289-297` (+9 ocorrências: 155, 158-160, 164-165, 174, 188, 192, 220, 224 — 22 queries no total)
**Description:** Toda query que recebe valor externo é montada por concatenação de string, inclusive o login (`"... WHERE email = '" + email + "' AND senha = '" + senha + "'"`) e a busca (`WHERE 1=1` + `query +=`). Confirmado por execução: `POST /login` com `{"email": "admin@loja.com' --", "senha": "qualquer"}` devolve 200 com o usuário Admin.
**Impact:** Qualquer anônimo entra como administrador sem senha, e a busca e os demais pontos permitem ler ou alterar qualquer tabela.
**Recommendation:** Trocar todas as 22 queries por placeholders `?` com tupla de parâmetros; a busca monta a lista de cláusulas e de parâmetros separadamente (→ PB-01).

### [CRITICAL] Endpoint perigoso exposto sem proteção (AP-02)
**File:** `app.py:47-57` (`POST /admin/reset-db`), `app.py:59-78` (`POST /admin/query`)
**Description:** `/admin/query` executa o SQL arbitrário recebido no corpo e devolve o resultado; `/admin/reset-db` apaga as quatro tabelas. Nenhum dos dois verifica identidade.
**Impact:** Um único `POST /admin/query` anônimo com `SELECT * FROM usuarios` devolve todas as senhas; outro com `DROP TABLE` destrói o banco.
**Recommendation:** Remover os dois endpoints — exceção de contrato declarada abaixo (→ PB-13).

### [CRITICAL] Autenticação ausente ou simulada (AP-07)
**File:** `controllers.py:167-183` (login), `app.py:11-30` (registro de todas as rotas, nenhuma com verificação)
**Description:** O login valida a senha e devolve o usuário sem emitir credencial alguma, e nenhuma rota lê header de autorização. Condição CRITICAL: há rotas anônimas que devolvem dado de outro usuário (`GET /usuarios`, `GET /usuarios/<id>`, `GET /pedidos`, `GET /pedidos/usuario/<id>`) e que fazem escrita destrutiva (`POST/PUT/DELETE /produtos`, `PUT /pedidos/<id>/status`).
**Impact:** Qualquer anônimo lista dados de todos os clientes, altera preço e estoque, apaga produtos e muda o status de qualquer pedido.
**Recommendation:** Login emite JWT HS256 assinado com `SECRET_KEY` do ambiente, expiração de 12h e `sub`/`role` no payload (PyJWT, dependência nova); middleware em `middlewares/auth.py` com três níveis — `requer_autenticacao`, `requer_admin`, `requer_dono_ou_admin` — aplicado rota por rota conforme a tabela em "Contract Exceptions" (→ PB-24).

### [CRITICAL] Dado sensível em resposta (AP-04)
**File:** `models.py:83` e `models.py:99` (campo `senha` nos dicts de usuário), `controllers.py:289` (`secret_key` no `/health`)
**Description:** `GET /usuarios` e `GET /usuarios/<id>` devolvem a senha de cada usuário; `GET /health` devolve a `SECRET_KEY` da aplicação.
**Impact:** Um `GET /usuarios` anônimo devolve a senha em claro de todos os usuários, e um `GET /health` entrega a chave que assina qualquer credencial futura.
**Recommendation:** Remover `senha` do serializer de usuário e `secret_key` do corpo do `/health`, resto dos objetos intacto — exceção de contrato declarada (→ PB-14).

### [CRITICAL] Hash de senha ausente (AP-05)
**File:** `database.py:31, 76-78` (coluna e seed em claro), `models.py:110` (comparação da senha dentro do SQL), `models.py:127-128` (gravação em claro)
**Description:** Senhas são gravadas e comparadas em texto puro.
**Impact:** Qualquer leitura do banco — por backup, pela injeção do AP-01 ou pelo AP-02 — expõe as senhas reais dos clientes, reutilizáveis em outros serviços.
**Recommendation:** `werkzeug.security.generate_password_hash` no cadastro e no seed, `check_password_hash` no login (busca por e-mail, verifica o hash na camada de serviço). Werkzeug já é dependência do Flask — nenhuma dependência nova. Não há banco legado versionado (`loja.db` não existe no repositório), então não há migração de senhas antigas a fazer; o seed é recriado com hash e as mesmas senhas de exemplo continuam funcionando no login (→ PB-05).

### [CRITICAL] Modo debug habilitado em bind público (AP-08)
**File:** `app.py:8`, `app.py:88`
**Description:** `app.config["DEBUG"] = True` e `app.run(host="0.0.0.0", port=5000, debug=True)` fixos no código.
**Impact:** O console interativo do Werkzeug fica acessível a qualquer máquina da rede — execução remota de código.
**Recommendation:** `DEBUG`, `HOST` e `PORT` lidos do ambiente em `config/settings.py`, com defaults `false`, `127.0.0.1` e `5000` (→ PB-02).

### [CRITICAL] Segredo hardcoded (AP-03)
**File:** `app.py:7`, `controllers.py:289`
**Description:** `SECRET_KEY = "minha-chave-super-secreta-123"` literal no código e repetida no corpo do `/health`.
**Impact:** Com o JWT do AP-07, uma chave conhecida permitiria a qualquer um forjar token de admin.
**Recommendation:** `SECRET_KEY` lida do ambiente; ausente, gera chave efêmera no boot e registra `warning` em voz alta (o projeto precisa rodar recém-clonado); `.env.example` versionado sem valores. O seed de desenvolvimento continua criando `admin@loja.com`/`admin123` — é dado de exemplo do README, e passa a ser semeado por chamada explícita no boot (ver AP-25), não por qualquer import (→ PB-02).

### [CRITICAL] Dependência com CVE conhecido em mecanismo usado de forma permissiva (AP-19)
**File:** `requirements.txt:2` (`flask-cors==5.0.1`), `requirements.txt:1` (`flask==3.1.1`), uso em `app.py:9`
**Description:** flask-cors 5.0.1 tem CVE-2024-6866, CVE-2024-6839 e CVE-2024-6844 (casamento de path/origem inconsistente; corrigidos em 6.0.0; corrente 6.0.5), e o projeto usa CORS liberado para todas as origens — condição CRITICAL do catálogo. flask 3.1.1 tem CVE-2026-27205 (LOW, `Vary: Cookie` ausente; corrigido em 3.1.3). Werkzeug 3.1.9: sem CVE no OSV. Boot sem `DeprecationWarning`.
**Impact:** As falhas de casamento de origem se somam à configuração permissiva, e qualquer restrição de CORS aplicada no futuro herdaria o bypass.
**Recommendation:** Atualizar para `flask==3.1.3` e `flask-cors==6.0.5`; adicionar `PyJWT` fixado (AP-07) (→ PB-11).

### [CRITICAL] God module com acesso a dados e roteamento HTTP no mesmo arquivo (AP-06)
**File:** `app.py:1-88`, `controllers.py:1-292`
**Description:** Condição CRITICAL: `app.py` registra rotas e executa SQL bruto (`app.py:49-55, 66-76`); `controllers.py` trata HTTP, valida regra de domínio, dispara notificação e consulta o banco diretamente (`controllers.py:266-274`), atendendo quatro domínios (produtos, usuários, pedidos, relatórios).
**Impact:** Nenhuma regra é testável sem subir HTTP e banco juntos, e qualquer mudança num domínio toca o arquivo dos outros três.
**Recommendation:** Reestruturação completa: `config/`, `database/` (conexão, schema, seed), `models/` (acesso a dados por domínio), `services/` (regra), `controllers/` (HTTP), `views/` (Blueprints por domínio), `middlewares/` (erro e auth), e um composition root em `app.py` (→ PB-03, PB-09).

### [HIGH] God module de dados e regra (AP-06)
**File:** `models.py:1-314`
**Description:** Condição HIGH: concentra query e regra de negócio (sem roteamento) para quatro domínios — produtos, usuários, pedidos e relatório.
**Impact:** A regra de desconto e a de estoque só são testáveis com SQLite real, e o arquivo cresce a cada domínio novo.
**Recommendation:** Dividir em `models/produto_model.py`, `usuario_model.py`, `pedido_model.py`, `relatorio_model.py` contendo só acesso a dados; regras vão para `services/` (→ PB-03).

### [HIGH] Regra de negócio na camada errada (AP-09)
**File:** camada de dados: `models.py:139-146` (checagem de estoque e cálculo do total do pedido), `models.py:256-262` (faixas de desconto do relatório); camada HTTP: `controllers.py:43-54` e `87-90` (validação de domínio do produto), `controllers.py:242` (status válidos)
**Description:** O model decide estoque suficiente e desconto por faixa de faturamento; o controller decide categorias válidas, limites de nome e status permitidos. A regra de pedido também não valida quantidade: confirmado por execução, `quantidade: -2` cria pedido com `total: -11999.98` e *aumenta* o estoque de 10 para 12.
**Impact:** Regras espalhadas entre transporte e persistência não podem ser testadas isoladamente, e a ausência de validação de quantidade permite fabricar estoque e faturamento negativo.
**Recommendation:** Mover para `services/`: `pedido_service` (verifica produto, estoque, calcula total; passa a exigir `produto_id` presente e `quantidade` inteira positiva → 400), `relatorio_service` (desconto por faixa), `produto_service` (validação do produto), com constantes em `models/constants.py`. Mudança de status por quantidade inválida declarada em "Contract Exceptions" (→ PB-04).

### [HIGH] Escrita multi-entidade sem transação (AP-10)
**File:** `models.py:148-168`
**Description:** Inserir pedido, inserir itens e debitar estoque acontecem com um único `commit` no fim e nenhum `rollback`; a checagem de estoque (linha 144) e o débito (linhas 163-166) são separados, sem guarda.
**Impact:** Uma exceção no meio deixa escritas pendentes na conexão global compartilhada, que são gravadas pelo `commit` da próxima requisição de outro cliente — pedido sem itens ou estoque debitado sem venda; e duas compras simultâneas vendem a mesma unidade.
**Recommendation:** Transação explícita com `rollback` no caminho de erro; débito com `UPDATE ... SET estoque = estoque - ? WHERE id = ? AND estoque >= ?` conferindo `rowcount` (→ PB-07).

### [HIGH] Estado global mutável (AP-11)
**File:** `database.py:4-11`
**Description:** Conexão SQLite única em variável global, aberta com `check_same_thread=False` e compartilhada por todas as requisições e threads.
**Impact:** Transações de requisições concorrentes se misturam na mesma conexão (ver AP-10), e o módulo não pode ser testado com banco isolado.
**Recommendation:** Conexão por requisição guardada em `flask.g`, fechada em `teardown_appcontext`; caminho do banco vindo de `settings` (→ PB-04).

### [HIGH] Efeito colateral escondido no fluxo (AP-12)
**File:** `controllers.py:208-210`, `controllers.py:247-250`
**Description:** O handler de criação de pedido "envia" e-mail, SMS e push, e o de status dispara notificações — nada disso anunciado pela rota nem isolado do transporte.
**Impact:** Quando as integrações forem reais, cada uma vai nascer dentro de um handler HTTP, sem possibilidade de teste ou de troca.
**Recommendation:** Extrair para `services/notificacao_service.py`, chamado pelo `pedido_service` após o commit (→ PB-04).

### [HIGH] Acesso a dados sem camada própria (AP-13)
**File:** `controllers.py:3, 266-274` (`health_check` consulta o banco), `app.py:4, 49-55, 66-76`
**Description:** O controller e o arquivo de rotas importam `get_db` e executam SQL diretamente.
**Impact:** A camada HTTP fica acoplada ao driver, e trocar o banco exige editar handlers.
**Recommendation:** Contagens do `/health` vão para um model de sistema; os endpoints admin são removidos (AP-02) (→ PB-03).

### [HIGH] Integração de notificação substituída por stub (AP-33)
**File:** `controllers.py:208-210`, `controllers.py:249-250`
**Description:** Condição HIGH (não decide dinheiro, acesso nem identidade): "ENVIANDO EMAIL/SMS/PUSH" é só `print`. O cancelamento imprime "Devolver estoque." mas nenhum estoque é devolvido.
**Impact:** O sistema parece notificar clientes e repor estoque, e não faz nenhum dos dois, sem erro em log.
**Recommendation:** Stub explícito, isolado e ruidoso: `NotificacaoService` com nome e comentário de stub, `logger.warning` no boot avisando que não há provedor configurado, mensagens via logger. Fica em `REQUER DECISÃO DE PRODUTO` (provedor, devolução de estoque no cancelamento) (→ PB-23).

### [MEDIUM] Queries N+1 (AP-17)
**File:** `models.py:187-193` e `models.py:219-225` (`cursor2`/`cursor3` dentro de laço), `models.py:139-141` e `154-156` (produto consultado por item, duas vezes)
**Description:** `GET /pedidos` e `GET /pedidos/usuario/<id>` fazem 1 + N + N·M queries; a criação de pedido consulta cada produto duas vezes.
**Impact:** O custo da listagem cresce com pedidos × itens; 100 pedidos de 3 itens são 401 queries.
**Recommendation:** Uma query com `JOIN` itens/produtos (`LEFT JOIN` para preservar `"Desconhecido"`), ordenada por pedido e item, agrupada em memória; na criação, uma leitura por produto reaproveitada (→ PB-06).

### [MEDIUM] Duplicação entre handlers irmãos, já divergida (AP-20)
**File:** `controllers.py:26-54` (criar) vs `controllers.py:66-90` (atualizar)
**Description:** Os blocos de validação de produto são cópias, e já divergiram: o atualizar não confere tamanho de nome nem categoria. Confirmado por execução: `PUT /produtos/2` com `nome: "A"` e `categoria: "xyz"` devolve 200.
**Impact:** A regra de catálogo depende da rota usada, e dados que o cadastro rejeita entram pela edição.
**Recommendation:** Um único validador em `produto_service` usado pelos dois; o PUT passa a aplicar as mesmas regras do POST — divergência de conserto declarada (→ PB-12).

### [MEDIUM] Tratamento de erro repetido sem handler central (AP-21)
**File:** `controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292`; `app.py:77-78`
**Description:** O mesmo `except Exception as e: return jsonify({"erro": str(e)}), 500` em 17 pontos, devolvendo a mensagem crua da exceção. Corpo ausente ou não-JSON vira 500 (confirmado: `POST /login` sem corpo → 500 `"'NoneType' object has no attribute 'get'"`; sem `Content-Type` → 500 `"415 Unsupported Media Type: ..."`).
**Impact:** Erro do cliente é reportado como falha do servidor, e detalhes internos vazam no corpo.
**Recommendation:** `middlewares/error_handler.py` com exceções de domínio mapeadas para status, `logger.exception` no 500 e corpo genérico; leitura de JSON tolerante (`get_json(silent=True)`). Rotas afetadas enumeradas em "Contract Exceptions" (→ PB-08).

### [MEDIUM] Contrato de resposta sem serializer único (AP-22)
**File:** produto: `models.py:12-21, 31-40, 304-313`; usuário: `models.py:79-86, 95-102, 114-119`; pedido: `models.py:178-185, 211-218` e itens `194-199, 226-231`
**Description:** Cada entidade é montada campo a campo em dois ou três pontos.
**Impact:** Remover a senha (AP-04) exigiria lembrar de dois lugares; esquecer um mantém o vazamento.
**Recommendation:** Um serializer por entidade em `models/serializers.py`; o formato público de login (`id, nome, email, tipo`) continua distinto e nomeado (→ PB-12).

### [MEDIUM] Schema sem constraints de integridade (AP-23)
**File:** `database.py:14-53`
**Description:** Zero `NOT NULL`, zero `UNIQUE`, zero `FOREIGN KEY`. E-mail aceita duplicata (confirmado: `POST /usuarios` com `joao@email.com` → 201), embora o login use e-mail como identidade.
**Impact:** Dois usuários com o mesmo e-mail tornam o login ambíguo, e pedidos podem apontar para usuário inexistente.
**Recommendation:** `NOT NULL` nas colunas que o código trata como obrigatórias; `UNIQUE` em `usuarios.email`; `FOREIGN KEY` em `pedidos.usuario_id → usuarios(id)` e `itens_pedido.pedido_id → pedidos(id)`; `PRAGMA foreign_keys = ON` por conexão. A FK `itens_pedido.produto_id → produtos(id)` **não** será criada — ver AP-24 em "Requires Product Decision" (→ PB-17).

### [MEDIUM] Limpeza em cascata ausente (AP-24)
**File:** `controllers.py:98-109`, `models.py:65-70`
**Description:** `DELETE /produtos/<id>` apaga o produto sem tratar os itens de pedido que o referenciam. Confirmado por execução: após apagar o produto 10, `GET /pedidos/usuario/2` devolve o item com `"produto_nome": "Desconhecido"`.
**Impact:** O histórico de vendas perde a identificação do que foi vendido.
**Recommendation:** Decidir o tratamento de produto com histórico — ver "Requires Product Decision". Comportamento atual preservado (→ PB-17).

### [MEDIUM] Bootstrap acoplado à inicialização (AP-25)
**File:** `database.py:14-84`
**Description:** `get_db()` cria o schema e insere produtos e usuários de exemplo (incluindo o admin) na primeira obtenção de conexão.
**Impact:** Qualquer ambiente que importe o módulo ganha dados fictícios e um admin com senha conhecida.
**Recommendation:** Separar `database/connection.py`, `database/schema.py` e `database/seed.py`; o composition root chama `criar_schema()` e, se `SEED_ON_BOOT` (default `true`, preserva o README e o baseline), `popular_dados_exemplo()` explicitamente (→ PB-18).

### [MEDIUM] CORS irrestrito (AP-26)
**File:** `app.py:9`
**Description:** `CORS(app)` libera todas as origens.
**Impact:** Qualquer site pode chamar a API a partir do navegador de um usuário.
**Recommendation:** Origens lidas de `CORS_ORIGINS` em `settings`; sem a variável, mantém `*` (contrato atual) com `logger.warning` no boot. A lista de origens é decisão de produto (→ PB-02).

### [LOW] Magic numbers, literais repetidos e metadado incoerente (AP-27)
**File:** `models.py:257-262` (faixas 10000/5000/1000 e 0.1/0.05/0.02), `controllers.py:52` (categorias), `controllers.py:242` (status), `controllers.py:47-50` (limites de nome), `app.py:36` e `controllers.py:285` (versão `"1.0.0"` duplicada), `controllers.py:286-288` (`"ambiente": "producao"` junto com `"debug": True`)
**Description:** Valores de domínio cravados na lógica, e o `/health` se declara produção enquanto reporta debug ligado.
**Impact:** Mudar uma faixa de desconto ou um status exige caçar literais, e o endpoint de diagnóstico mente sobre o estado do serviço.
**Recommendation:** `models/constants.py` com `StatusPedido`, `CATEGORIAS_VALIDAS`, `FAIXAS_DESCONTO`, limites de nome e `VERSAO_API`; `ambiente`, `debug` e `db_path` do `/health` passam a refletir `settings` — divergência de `debug` declarada (→ PB-19).

### [LOW] `print` como logging (AP-28)
**File:** `controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250`; `app.py:56, 83-86`
**Description:** Diagnóstico, auditoria e erro saem por `print`, sem nível nem destino.
**Impact:** Falhas não são filtráveis nem coletáveis em produção.
**Recommendation:** `config/logging_config.py` com `logging` padrão; `info` para evento de negócio, `exception` para falha (→ PB-20).

### [LOW] Nomes não descritivos (AP-29)
**File:** `models.py:187, 191, 219, 223` (`cursor2`, `cursor3`); parâmetro `id` sombreando o builtin em `controllers.py:14, 64, 98, 136` e `models.py:24, 54, 65, 89`
**Description:** Cursores numerados e `id` como nome de parâmetro.
**Impact:** Leitura mais lenta e builtin inacessível nessas funções.
**Recommendation:** Cursores numerados desaparecem com o JOIN (AP-17); parâmetros internos renomeados para `produto_id`/`usuario_id` — os caminhos das rotas não mudam (→ PB-19).

### [LOW] Imports mortos (AP-30)
**File:** `database.py:2` (`import os`), `models.py:2` (`import sqlite3`)
**Description:** Dois imports nunca usados nos respectivos arquivos (contagem de símbolos rodada; `index`, `reset_database` e `executar_query` aparecem com contagem 1 mas são handlers registrados por decorator, não código morto).
**Impact:** Ruído que sugere dependência inexistente.
**Recommendation:** Remover (→ PB-21).

### [LOW] Ausência de paginação (AP-31)
**File:** `models.py:7` (`GET /produtos`), `models.py:75` (`GET /usuarios`), `models.py:206` (`GET /pedidos`), `models.py:174` (`GET /pedidos/usuario/<id>`)
**Description:** As listagens carregam a tabela inteira, sem `LIMIT`.
**Impact:** O tempo de resposta e a memória crescem linearmente com a base.
**Recommendation:** `limit`/`offset` opcionais nas quatro listagens, com `ORDER BY id`; sem os parâmetros, devolve a lista inteira como hoje (contrato preservado). O tamanho de página padrão fica em decisão de produto (→ PB-22).

### [LOW] Verbosidade evitável (AP-32)
**File:** `controllers.py:8, 57, 106, 161, 179, 208` (concatenação com `str()`), `controllers.py:200` (`not itens or len(itens) == 0`), `models.py:63, 70, 283` (`return True` sem uso)
**Description:** Construções longas para o que a linguagem expressa direto.
**Impact:** Mais código para ler sem ganho.
**Recommendation:** f-strings, `if not itens`, retornos inúteis removidos (→ PB-19).

## Contract Exceptions

**Exceções das quatro classes permitidas:**

- `app.py:59-78` — endpoint `POST /admin/query` removido (AP-02)
- `app.py:47-57` — endpoint `POST /admin/reset-db` removido (AP-02)
- `models.py:83, 99` — campo `senha` removido das respostas de `GET /usuarios` e `GET /usuarios/<id>`, resto do objeto intacto (AP-04)
- `controllers.py:289` — campo `secret_key` removido do corpo de `GET /health`, resto do objeto intacto (AP-04)
- `controllers.py:180` — `POST /login` bem-sucedido ganha o campo de topo `token` (JWT); `dados`, `sucesso` e `mensagem` idênticos (AP-07)
- rotas e nível de acesso (AP-07). Anônimo em rota protegida: 200 → **401** `{"erro": ...}`; autenticado sem o papel ou sem ser dono: **403** `{"erro": ...}`. Autenticado com o nível exigido recebe exatamente o que recebia antes:
    - `GET    /`                               público        — raiz, sem dado de usuário
    - `GET    /health`                         público        — liveness, sem dado de usuário
    - `GET    /produtos`                       público        — catálogo
    - `GET    /produtos/busca`                 público        — catálogo
    - `GET    /produtos/<id>`                  público        — catálogo
    - `POST   /produtos`                       admin          — escrita no catálogo (ver nota abaixo)
    - `PUT    /produtos/<id>`                  admin          — altera preço e estoque do catálogo (ver nota abaixo)
    - `DELETE /produtos/<id>`                  admin          — apaga item do catálogo (ver nota abaixo)
    - `GET    /usuarios`                       admin          — lista nome e e-mail de todos os usuários
    - `GET    /usuarios/<id>`                  dono ou admin  — dado de um usuário específico
    - `POST   /usuarios`                       público        — cadastro, único caminho de entrada no sistema
    - `POST   /login`                          público        — emite a credencial
    - `POST   /pedidos`                        dono ou admin  — exige credencial, e o `usuario_id` do corpo precisa ser o `sub` do token (admin pode qualquer um); sem isso um cliente cria pedido em nome de outro e debita estoque. Não é o único caminho de entrada: o cadastro é público e existe independentemente. Validações de corpo (400) continuam antes da checagem de dono.
    - `GET    /pedidos`                        admin          — pedidos de todos os usuários
    - `GET    /pedidos/usuario/<usuario_id>`   dono ou admin  — pedidos de um usuário específico
    - `PUT    /pedidos/<pedido_id>/status`     admin          — aprovar, enviar, entregar e cancelar são operações da loja; com credencial simples o cliente marcaria o próprio pedido como aprovado ou entregue
    - `GET    /relatorios/vendas`              admin          — relatório agregado de faturamento
  - **Nota sobre `/produtos` (desvio deliberado da tabela do PB-24, que prevê "credencial" para escrita em catálogo):** o cadastro é público, então "credencial" custa uma requisição — qualquer cliente recém-cadastrado poderia pôr o preço de um produto em 0,01 e comprá-lo. O próprio sistema já distingue o papel `admin` (`usuarios.tipo`), então a escrita no catálogo exige admin.

**Divergências por conserto de bug** — não pertencem às quatro classes acima; mudam status ou corpo de caminhos que hoje se comportam errado. Listadas com os dois valores para aprovação explícita; se alguma for vetada, a Fase 3 preserva o comportamento atual dela:

- Corpo JSON ausente, `null` ou sem `Content-Type: application/json` (AP-21) — hoje 500 com a mensagem crua da exceção; passa a 400:
    - `POST /produtos` → 400 `{"erro": "Dados inválidos"}`
    - `PUT /produtos/<id>` → 400 `{"erro": "Dados inválidos"}` (o 404 de produto inexistente continua vindo antes)
    - `POST /usuarios` → 400 `{"erro": "Dados inválidos"}`
    - `POST /login` → 400 `{"erro": "Email e senha são obrigatórios"}`
    - `POST /pedidos` → 400 `{"erro": "Dados inválidos"}`
    - `PUT /pedidos/<pedido_id>/status` → 400 `{"erro": "Status inválido"}`
- Tipos inválidos (AP-09/AP-20) — hoje 500 com `TypeError`/`ValueError`; passa a 400 com mensagem do campo: `preco`/`estoque` não numérico ou `nome` não-string em `POST /produtos` e `PUT /produtos/<id>`; `preco_min`/`preco_max` não numérico em `GET /produtos/busca`.
- Qualquer outro erro inesperado, em qualquer rota (AP-21) — continua 500, mas o corpo passa de `{"erro": "<str(e)>"}` para `{"erro": "Erro interno do servidor"}`; no `/health`, de `{"status": "erro", "detalhes": "<str(e)>"}` para `{"status": "erro", "detalhes": "Erro interno do servidor"}`. A exceção vai para o log.
- `PUT /produtos/<id>` com nome < 2 ou > 200 caracteres, ou categoria fora da lista (AP-20) — hoje 200; passa a 400 com as mesmas mensagens do `POST`.
- `POST /pedidos` com item sem `produto_id` (hoje 500 `KeyError`) ou `quantidade` não inteira ou ≤ 0 (hoje 201 com total negativo e estoque aumentado) (AP-09) — passa a 400.
- `POST /usuarios` com e-mail já cadastrado (AP-23) — hoje 201; passa a 409 `{"erro": "Email já cadastrado"}`.
- `POST /pedidos` feito por admin com `usuario_id` inexistente (AP-23) — hoje 201 com pedido órfão; passa a 400 `{"erro": "Usuário não encontrado"}`.
- `GET /health`, campo `debug` (AP-27/AP-08) — hoje `true` fixo; passa a refletir o estado real (`false` com o default). `ambiente` (`"producao"`) e `db_path` (`"loja.db"`) mantêm os valores atuais nos defaults, agora lidos de `settings`.

## Requires Product Decision

- **AP-33** — Integração de notificação: qual provedor de e-mail/SMS/push contratar; se o cancelamento deve devolver o estoque e a partir de quais status (hoje a mensagem anuncia e nada acontece); quais transições de status são válidas (hoje qualquer status vai para qualquer outro, inclusive `entregue → pendente`). A Fase 3 isola e nomeia o stub, sem mudar comportamento.
- **AP-24** — Produto com histórico de vendas: bloquear a exclusão (409), apagar em cascata, ou exclusão lógica pela coluna `ativo`, que existe no schema e nunca é usada. Até a decisão, comportamento atual preservado e a FK `itens_pedido.produto_id` não é criada.
- **AP-26** (parcial) — Quais origens o CORS deve liberar. O mecanismo (`CORS_ORIGINS`) é entregue; o default `*` preserva o contrato atual.
- **AP-31** (parcial) — Tamanho de página padrão das listagens. `limit`/`offset` opcionais são entregues; sem eles, a lista inteira continua sendo devolvida.

================================
Total: 30 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
