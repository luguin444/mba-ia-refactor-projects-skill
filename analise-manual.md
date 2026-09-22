# Análise Manual

Achados por projeto, classificados pela escala de severidade do desafio.

---

## Projeto 1 — code-smells-project (Python/Flask)

4 arquivos · ~780 linhas · Flask 3.1.1 + flask-cors · SQLite

**Resumo:** CRITICAL: 6 | HIGH: 6 | MEDIUM: 8 | LOW: 6 — total 26

### CRITICAL

#### [CRITICAL] SQL Injection generalizado
**File:** `models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 148-166, 174, 188, 192, 279-281, 289-297`
**Descrição:** Praticamente toda query é montada por concatenação de string com input do usuário; `login_usuario:109` permite bypass de autenticação com `' OR '1'='1`.
**Impacto:** Leitura, alteração e destruição arbitrária do banco por qualquer cliente HTTP. Ironicamente `database.py:70-83` usa placeholders `?` corretamente nos seeds — o padrão certo existe no projeto e foi ignorado.

#### [CRITICAL] Endpoint de execução de SQL arbitrário
**File:** `app.py:59-78`
**Descrição:** `POST /admin/query` executa qualquer SQL vindo do body, sem autenticação.
**Impacto:** Equivale a dar acesso de DBA à internet — `DROP TABLE`, dump de senhas, ou uma query pesada que trava o processo single-thread.

#### [CRITICAL] Endpoint destrutivo sem autenticação
**File:** `app.py:47-57`
**Descrição:** `POST /admin/reset-db` apaga as 4 tabelas do banco sem nenhuma verificação de identidade.
**Impacto:** Perda total de dados disparada por qualquer requisição anônima.

#### [CRITICAL] Segredos hardcoded e configuração insegura
**File:** `app.py:7-8, 88` · `controllers.py:288-289`
**Descrição:** `SECRET_KEY` fixa no código, `DEBUG=True`, e o `/health` devolve a própria secret key no corpo da resposta.
**Impacto:** Werkzeug debugger exposto em `0.0.0.0` permite execução remota de código; a secret vazada permite forjar sessões.

#### [CRITICAL] Senhas em texto plano e expostas pela API
**File:** `models.py:122-131, 105-120` · `database.py:75-83` · `models.py:84, 100`
**Descrição:** Senhas são gravadas e comparadas sem hash, e `get_todos_usuarios`/`get_usuario_por_id` incluem o campo `senha` no retorno.
**Impacto:** Um `GET /usuarios` anônimo devolve a senha de todos os usuários — vazamento direto de credenciais.

#### [CRITICAL] God module: ausência total de camadas
**File:** `models.py:1-314` · `controllers.py:1-292`
**Descrição:** `models.py` concentra acesso a dados, regra de negócio e formatação de resposta de 4 domínios (produtos, usuários, pedidos, relatórios); `controllers.py` faz o mesmo do lado HTTP.
**Impacto:** Nada pode ser testado em isolamento e qualquer mudança em um domínio arrisca os outros três.

### HIGH

#### [HIGH] Ausência de autenticação e autorização
**File:** `app.py:11-30` · `controllers.py:167-186`
**Descrição:** Nenhuma rota exige identidade; o `login` valida a senha mas não emite token nem sessão, então o resultado não protege nada.
**Impacto:** Qualquer cliente altera preços, deleta produtos e muda status de pedidos alheios.

#### [HIGH] Regra de negócio dentro da camada de dados
**File:** `models.py:133-169, 235-273`
**Descrição:** `criar_pedido` calcula total e valida estoque, e `relatorio_vendas` aplica faixas de desconto — tudo dentro de funções de repositório.
**Impacto:** Testar a regra de desconto exige um banco real; trocar de persistência levaria a regra junto.

#### [HIGH] Conexão global mutável compartilhada
**File:** `database.py:4-11`
**Descrição:** Singleton global de conexão SQLite com `check_same_thread=False` e sem lock.
**Impacto:** Cursores concorrentes sobre a mesma conexão geram race conditions, e não há como injetar um banco de teste.

#### [HIGH] Escrita multi-tabela sem transação nem rollback
**File:** `models.py:133-169`
**Descrição:** `criar_pedido` insere o pedido, insere os itens e debita estoque com um único `commit` no fim e nenhum `try/except` com rollback.
**Impacto:** Uma falha no meio do loop deixa pedido sem itens ou estoque debitado sem venda registrada.

#### [HIGH] Efeitos colaterais de negócio embutidos no controller
**File:** `controllers.py:208-210, 247-250`
**Descrição:** Envio de e-mail, SMS e push é simulado com `print` dentro do handler HTTP.
**Impacto:** Notificação vira responsabilidade do controller — quando virar integração real, o handler passa a depender de rede e a rota fica lenta e frágil.

#### [HIGH] Roteamento manual sem Blueprints
**File:** `app.py:11-30`
**Descrição:** As 15 rotas dos 4 domínios são registradas uma a uma via `add_url_rule` no entry point.
**Impacto:** O entry point vira ponto de conflito de merge e não existe fronteira por domínio — o Flask oferece Blueprints exatamente para isso.

### MEDIUM

#### [MEDIUM] Queries N+1 na listagem de pedidos
**File:** `models.py:171-201, 203-233`
**Descrição:** Para cada pedido roda-se uma query de itens, e para cada item uma query de nome de produto.
**Impacto:** 50 pedidos com 3 itens = 201 queries onde 1 `JOIN` resolveria.

#### [MEDIUM] Duplicação de código entre funções irmãs
**File:** `models.py:171-201` vs `203-233` · `models.py:4-22, 24-41, 300-314`
**Descrição:** `get_pedidos_usuario` e `get_todos_pedidos` são o mesmo bloco de ~30 linhas mudando só o `WHERE`, e o mapeamento row→dict de produto está copiado em 3 lugares.
**Impacto:** Toda alteração de contrato precisa ser feita em N lugares e alguma sempre é esquecida.

#### [MEDIUM] Validação duplicada entre criar e atualizar
**File:** `controllers.py:28-54` vs `72-90`
**Descrição:** O mesmo bloco de validações de produto está copiado nos dois handlers, e o de `atualizar` já perdeu as regras de tamanho de nome e categoria válida.
**Impacto:** As duas rotas já divergiram — dá para criar via PUT um produto que o POST rejeitaria.

#### [MEDIUM] Tratamento de erro repetido que vaza detalhe interno
**File:** `controllers.py` — 17 blocos `except Exception as e: ... str(e)`
**Descrição:** Cada handler repete o mesmo `try/except` genérico e devolve a mensagem crua da exceção ao cliente.
**Impacto:** Mensagens de erro do SQLite chegam ao usuário final revelando schema, e bugs reais ficam mascarados como 500 sem log estruturado.

#### [MEDIUM] Contrato de resposta montado à mão
**File:** `models.py:12-21, 31-40, 79-86, 95-102` · `controllers.py` (todos os `jsonify`)
**Descrição:** Cada função monta o dicionário de resposta literalmente, sem serializer ou schema.
**Impacto:** Um typo em uma chave quebra o cliente silenciosamente, e não há fonte única de verdade do formato da API.

#### [MEDIUM] Seeds acoplados à obtenção de conexão
**File:** `database.py:7-86`
**Descrição:** `get_db()` cria conexão, roda o DDL das 4 tabelas e insere dados de exemplo na mesma função.
**Impacto:** Dados fictícios são inseridos em qualquer ambiente que chamar `get_db()`, incluindo produção.

#### [MEDIUM] CORS liberado para qualquer origem
**File:** `app.py:9`
**Descrição:** `CORS(app)` sem restrição de origens, métodos ou headers.
**Impacto:** Qualquer site consegue chamar a API a partir do navegador da vítima.

#### [MEDIUM] Schema sem constraints de integridade
**File:** `database.py:14-53`
**Descrição:** Nenhuma coluna tem `NOT NULL`, `email` não é `UNIQUE` e não há `FOREIGN KEY` em `pedidos.usuario_id` nem em `itens_pedido`.
**Impacto:** O banco aceita pedidos órfãos e e-mails duplicados, e a aplicação não compensa isso com validação.

### LOW

#### [LOW] Sem paginação nas listagens
**File:** `models.py:4-22, 72-87, 203-233`
**Descrição:** `SELECT *` sem `LIMIT` nas rotas de listar produtos, usuários e pedidos.
**Impacto:** O tempo de resposta cresce linearmente com a tabela até virar timeout.

#### [LOW] Magic numbers espalhados
**File:** `models.py:257-262` · `controllers.py:47-50, 52, 242`
**Descrição:** Faixas de desconto (10000/5000/1000 e 0.1/0.05/0.02), limites de tamanho de nome e as listas de categorias e status válidos estão cravados no meio da lógica.
**Impacto:** Regra de negócio invisível para quem lê o código e impossível de ajustar sem deploy.

#### [LOW] `print` usado como logging
**File:** `app.py:56, 83-86` · `controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250`
**Descrição:** Diagnóstico e auditoria saem por `print` em stdout, sem nível, timestamp ou destino configurável.
**Impacto:** Impossível filtrar por severidade ou enviar a um agregador de logs.

#### [LOW] Nomes de variáveis por numeração
**File:** `models.py:187, 191, 219, 223`
**Descrição:** `cursor`, `cursor2` e `cursor3` dentro dos loops aninhados.
**Impacto:** O nome não diz nada sobre o papel de cada cursor — e a numeração crescente é o próprio sintoma do N+1.

#### [LOW] Shadowing de builtin e imports mortos
**File:** `controllers.py:14, 64, 98` · `models.py:2, 24` · `database.py:2`
**Descrição:** `id` é usado como nome de parâmetro em 6 funções, e `import sqlite3` em `models.py` e `import os` em `database.py` nunca são usados.
**Impacto:** Ruído que confunde leitura e esconde o builtin `id()` no escopo da função.

#### [LOW] Metadados hardcoded e incoerentes
**File:** `app.py:36` · `controllers.py:285-288`
**Descrição:** A versão `"1.0.0"` está cravada em dois lugares e o `/health` se declara `"ambiente": "producao"` enquanto reporta `"debug": true`.
**Impacto:** O endpoint de saúde mente sobre o estado real do serviço.

### APIs deprecated

Nenhuma encontrada neste projeto — Flask 3.1.1 e `sqlite3` são usados com APIs atuais. A categoria deve permanecer no catálogo da skill e será exercitada nos projetos 2 e 3.

---

## Projeto 2 — ecommerce-api-legacy (Node.js/Express)

3 arquivos · ~180 linhas · Express 4.18.2 + sqlite3 5.1.6 · SQLite em memória

**Resumo:** CRITICAL: 6 | HIGH: 6 | MEDIUM: 7 | LOW: 5 — total 24

### CRITICAL

#### [CRITICAL] Número de cartão e chave de produção escritos no log
**File:** `src/AppManager.js:45`
**Descrição:** O handler de checkout loga o PAN completo do cartão junto com a `paymentGatewayKey` de produção em stdout.
**Impacto:** Violação direta de PCI-DSS — qualquer pessoa com acesso aos logs coleta cartões e a chave live do gateway.

#### [CRITICAL] Credenciais de produção hardcoded no repositório
**File:** `src/utils.js:2-4`
**Descrição:** Usuário e senha do banco e uma chave `pk_live_...` de gateway de pagamento estão literais no código versionado.
**Impacto:** Segredo commitado é segredo vazado: rotacionar exige reescrever o histórico do git e ainda assim ele já circulou.

#### [CRITICAL] Hash de senha caseiro e reversível
**File:** `src/utils.js:17-23` · `src/AppManager.js:18, 68`
**Descrição:** `badCrypto` concatena base64 do próprio input 10.000 vezes e trunca em 10 caracteres, sem salt; o seed grava a senha `'123'` em texto plano.
**Impacto:** O espaço de saída é minúsculo e determinístico — colisão e reversão por dicionário são triviais, e o custo do loop dá a falsa impressão de segurança.

#### [CRITICAL] Aprovação de pagamento decidida pelo primeiro dígito do cartão
**File:** `src/AppManager.js:46`
**Descrição:** `cc.startsWith("4") ? "PAID" : "DENIED"` substitui a integração com o gateway.
**Impacto:** Qualquer número começando com 4 gera matrícula paga sem transação real — receita fantasma e curso liberado de graça.

#### [CRITICAL] Nenhuma rota exige autenticação
**File:** `src/AppManager.js:28, 80, 131`
**Descrição:** As três rotas são públicas, incluindo `/api/admin/financial-report`, que devolve nome, e-mail e valores pagos de todos os alunos, e o `DELETE /api/users/:id`.
**Impacto:** Vazamento de PII e faturamento por uma requisição anônima, e qualquer um remove usuários do sistema.

#### [CRITICAL] God Class: banco, schema, seeds, rotas e negócio na mesma classe
**File:** `src/AppManager.js:4-141`
**Descrição:** `AppManager` abre a conexão, cria as 5 tabelas, insere seeds, registra as rotas e implementa checkout, pagamento e auditoria.
**Impacto:** Zero separação de camadas — nada é testável isoladamente e o nome da classe já denuncia que ela não tem responsabilidade definida.

### HIGH

#### [HIGH] Regra de negócio inline dentro do handler HTTP
**File:** `src/AppManager.js:28-78`
**Descrição:** O handler de checkout tem 50 linhas e define `processPaymentAndEnroll` como closure interna, misturando parsing de request, cobrança, matrícula e auditoria.
**Impacto:** A regra de checkout só existe acoplada ao Express — não dá para reusar, testar ou chamar por outro canal.

#### [HIGH] Cadastro de usuário escondido dentro do fluxo de checkout
**File:** `src/AppManager.js:66-72`
**Descrição:** Se o e-mail não existe, o checkout cria a conta silenciosamente com a senha enviada no mesmo payload, ou com o default `"123456"`.
**Impacto:** Efeito colateral invisível no contrato da rota, e um checkout com senha omitida gera uma conta com senha conhecida por todos.

#### [HIGH] Escrita em três tabelas sem transação
**File:** `src/AppManager.js:50-62`
**Descrição:** Matrícula, pagamento e log de auditoria são inseridos em callbacks aninhados, sem `BEGIN`/`COMMIT` e sem rollback.
**Impacto:** Uma falha no meio deixa matrícula sem pagamento registrado — exatamente o estado inconsistente que o checkout não pode produzir.

#### [HIGH] Callback hell com controle de fluxo manual
**File:** `src/AppManager.js:37-77` (5 níveis) · `src/AppManager.js:83-128` (4 níveis)
**Descrição:** O relatório coordena o assíncrono com contadores decrementados à mão (`coursesPending`, `enrPending`) para decidir quando responder.
**Impacto:** Se qualquer callback falhar, o contador nunca zera e a requisição fica pendurada até o timeout do cliente.

#### [HIGH] Erros de banco silenciosamente engolidos
**File:** `src/AppManager.js:57, 104, 106, 133`
**Descrição:** Vários callbacks recebem `err` e nunca o checam — o `DELETE` responde 200 mesmo se a query falhar.
**Impacto:** Falhas viram sucesso aparente para o cliente e desaparecem sem registro.

#### [HIGH] Estado global mutável exportado do módulo
**File:** `src/utils.js:9-10, 25`
**Descrição:** `globalCache` cresce indefinidamente a cada checkout e `totalRevenue` é exportado por valor, então quem importa recebe uma cópia congelada em zero.
**Impacto:** Vazamento de memória no processo e um contador de receita que nunca poderia funcionar — bug latente disfarçado de feature.

### MEDIUM

#### [MEDIUM] Queries N+1 no relatório financeiro
**File:** `src/AppManager.js:83-128`
**Descrição:** Uma query por curso, mais uma por matrícula para buscar o aluno e outra para buscar o pagamento.
**Impacto:** 2 cursos com 50 matrículas geram 203 queries onde dois `JOIN` resolveriam.

#### [MEDIUM] Auditoria acoplada ao fluxo de negócio
**File:** `src/AppManager.js:57-61`
**Descrição:** O `INSERT` em `audit_logs` e a escrita no cache são feitos na mão dentro do callback de pagamento.
**Impacto:** Observabilidade vira responsabilidade do checkout — cada novo fluxo precisa lembrar de auditar, e alguém sempre esquece.

#### [MEDIUM] Dependências deprecated na árvore do projeto
**File:** `package.json:9-11` · `package-lock.json`
**Descrição:** `sqlite3@5.1.6` arrasta 7 pacotes marcados como deprecated no lock (`node-pre-gyp`, `glob`, `tar`, `rimraf`, `inflight` e outros), vários com CVE conhecido; Express 4 já tem sucessor estável na v5.
**Impacto:** Vulnerabilidades herdadas sem correção disponível na versão fixada — a substituição indicada é `node:sqlite` ou `better-sqlite3`.

#### [MEDIUM] Banco em memória recriado a cada boot
**File:** `src/AppManager.js:7, 10-23` · `src/app.js:9`
**Descrição:** A conexão é `:memory:` e o DDL mais os seeds rodam no start, em qualquer ambiente.
**Impacto:** Todo dado desaparece no restart e não há distinção entre migração, seed e bootstrap da aplicação.

#### [MEDIUM] Sem tratamento de erro centralizado e respostas inconsistentes
**File:** `src/app.js:1-14` · `src/AppManager.js:35, 38, 41`
**Descrição:** Não existe middleware de erro no Express, e os caminhos de falha devolvem texto puro (`"Erro DB"`) enquanto o sucesso devolve JSON.
**Impacto:** O cliente precisa adivinhar o formato da resposta pelo status code, e nenhuma exceção não capturada tem destino.

#### [MEDIUM] Verifica-e-insere sem unicidade no banco
**File:** `src/AppManager.js:40-72` · `src/AppManager.js:12`
**Descrição:** O checkout consulta o usuário por e-mail e depois insere, sem `UNIQUE` na coluna nem transação.
**Impacto:** Dois checkouts simultâneos do mesmo e-mail criam duas contas duplicadas.

#### [MEDIUM] Schema sem constraints e remoção que deixa órfãos
**File:** `src/AppManager.js:12-16, 131-137`
**Descrição:** Nenhuma tabela tem `NOT NULL`, `UNIQUE` ou `FOREIGN KEY`, e deletar um usuário não toca em matrículas e pagamentos.
**Impacto:** O banco acumula registros apontando para usuários inexistentes, e o relatório financeiro passa a contar receita de alunos "Unknown".

### LOW

#### [LOW] Nomes de variável de uma letra e contrato abreviado
**File:** `src/AppManager.js:29-33`
**Descrição:** `u`, `e`, `p`, `cid`, `cc` internamente, espelhando campos de API igualmente cifrados (`usr`, `eml`, `pwd`, `c_id`).
**Impacto:** O contrato público da rota é ilegível sem abrir o código, e `e` colide com a convenção de `error`.

#### [LOW] Três significados de `this` no mesmo método
**File:** `src/AppManager.js:26, 50-57, 69-71`
**Descrição:** `const self = this` convive com arrow functions que já preservam o `this`, e os callbacks `function(err)` do sqlite3 trazem um terceiro `this` (o do statement, usado em `this.lastID`).
**Impacto:** Quem lê precisa rastrear qual `this` está em escopo a cada nível de aninhamento.

#### [LOW] `let` usado para tudo, `const` em lugar nenhum
**File:** `src/AppManager.js:29-33, 81, 86, 90, 93`
**Descrição:** Valores que nunca são reatribuídos são declarados como `let`.
**Impacto:** Perde-se o sinal mais barato de intenção do JavaScript moderno sobre o que pode mudar.

#### [LOW] Mensagem de erro que confessa o bug ao usuário final
**File:** `src/AppManager.js:135`
**Descrição:** A resposta do `DELETE` é `"Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco."`.
**Impacto:** Documenta a falha para quem não deveria vê-la, em vez de corrigi-la ou registrá-la.

#### [LOW] Configuração de infraestrutura misturada com segredos
**File:** `src/utils.js:1-7`
**Descrição:** `port` convive no mesmo objeto literal que senha de banco e chave de pagamento, sem leitura de variáveis de ambiente.
**Impacto:** Não há como separar o que é configuração inofensiva do que nunca pode sair do cofre.

### APIs deprecated

O código-fonte não usa APIs deprecated de Node ou Express, mas a árvore de dependências carrega 7 pacotes marcados como deprecated pelo próprio npm (ver finding MEDIUM acima). É o primeiro projeto a exercitar essa categoria do catálogo — e mostra que o sinal de detecção precisa olhar o lockfile, não só o código.

---

## Projeto 3 — task-manager-api (Python/Flask)

15 arquivos · 1158 linhas · Flask 3.0 + SQLAlchemy 3.1 + marshmallow + CORS · SQLite

**Resumo:** CRITICAL: 6 | HIGH: 6 | MEDIUM: 8 | LOW: 6 — total 26

> **Leitura geral:** ao contrário dos projetos 1 e 2, aqui a estrutura existe — há `models/`, `routes/`, `services/`, `utils/`, Blueprints, ORM e hash de senha. O problema é que **a estrutura é decorativa**: `Task.is_overdue()`, `process_task_data()`, `NotificationService`, `validate_email()` e as constantes de `helpers.py` estão escritos e nunca são chamados, enquanto as rotas reimplementam tudo à mão. Pastas com o nome certo não garantem responsabilidade no lugar certo.

### CRITICAL

#### [CRITICAL] Senhas com MD5 sem salt
**File:** `models/user.py:29, 32`
**Descrição:** `set_password` e `check_password` usam `hashlib.md5` puro, sem salt e sem custo de derivação.
**Impacto:** MD5 está quebrado desde 2004 — uma rainbow table reverte as senhas em segundos, e o projeto parece seguro justamente por ter "criptografia".

#### [CRITICAL] Hash da senha devolvido pela API
**File:** `models/user.py:21` · `routes/user_routes.py:33, 85, 129, 209`
**Descrição:** `User.to_dict()` inclui o campo `password`, e esse dict é o corpo de resposta de `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e do `/login`.
**Impacto:** Quatro endpoints públicos entregam o hash de qualquer usuário — combinado com o MD5, é a senha em claro a um dicionário de distância.

#### [CRITICAL] Credenciais de SMTP hardcoded
**File:** `services/notification_service.py:7-10, 17`
**Descrição:** Host, usuário e a senha `'senha123'` da conta de e-mail estão literais no construtor do serviço.
**Impacto:** Quem lê o repositório assume a conta de envio da aplicação e passa a mandar e-mail em nome dela.

#### [CRITICAL] SECRET_KEY hardcoded e debug exposto na rede
**File:** `app.py:13, 34`
**Descrição:** `SECRET_KEY = 'super-secret-key-123'` no código e `app.run(debug=True, host='0.0.0.0')`.
**Impacto:** O console do Werkzeug fica acessível a qualquer host da rede, o que é execução remota de código — e a chave fixa permite forjar sessões assinadas.

#### [CRITICAL] Autenticação de fachada
**File:** `routes/user_routes.py:210` · todas as 17 rotas
**Descrição:** O `/login` devolve `'fake-jwt-token-' + str(user.id)` — um token previsível, sem assinatura e sem expiração — e nenhuma rota do projeto verifica token algum.
**Impacto:** A API aparenta ter autenticação e não tem: qualquer anônimo lê, edita e apaga tasks e usuários alheios.

#### [CRITICAL] Escalonamento de privilégio no cadastro público
**File:** `routes/user_routes.py:42-78`
**Descrição:** `POST /users` é aberto e aceita `role` vindo do corpo da requisição, validando apenas que o valor esteja em `['user', 'admin', 'manager']`.
**Impacto:** Qualquer pessoa cria a própria conta de admin — e como `is_admin()` nunca é chamado, o privilégio nem sequer serve de defesa, só de ilusão.

### HIGH

#### [HIGH] Regra de negócio reimplementada inline apesar de existir no model
**File:** `models/task.py:50-60` (definição, nunca chamada) · `routes/task_routes.py:30-39, 71-80, 283-287` · `routes/user_routes.py:171-180` · `routes/report_routes.py:33-37, 132-135`
**Descrição:** A regra de "task atrasada" está escrita como `Task.is_overdue()` e copiada manualmente em cinco lugares diferentes das rotas.
**Impacto:** Cinco cópias de uma regra que já tinha dono; mudar o critério de atraso exige encontrar todas, e o método do model vai continuar mentindo.

#### [HIGH] Validação duplicada e a camada que deveria centralizá-la está morta
**File:** `utils/helpers.py:57-108` (nunca chamada) · `routes/task_routes.py:89-144` vs `156-213` · `routes/user_routes.py:54-72` vs `102-125`
**Descrição:** `process_task_data()` existe para normalizar e validar payload de task, e as rotas de criar e atualizar reimplementam as mesmas regras, cada uma com pequenas divergências.
**Impacto:** `POST /tasks` rejeita prioridade não numérica com 400, `PUT /tasks/<id>` estoura 500 no mesmo caso — os contratos já divergiram.

#### [HIGH] Rotas acumulam controller, serviço e repositório
**File:** `routes/task_routes.py:1-299` · `routes/report_routes.py:12-101`
**Descrição:** Os blueprints montam query, aplicam regra de negócio, agregam estatística e serializam resposta; `summary_report` sozinho tem 90 linhas e 20 queries.
**Impacto:** Os arquivos de rota são os maiores do projeto — o sintoma clássico de que as camadas abaixo delas estão vazias.

#### [HIGH] Serialização remontada à mão apesar do `to_dict()`
**File:** `models/task.py:23-36` · `routes/task_routes.py:17-28` · `routes/user_routes.py:162-169`
**Descrição:** `Task.to_dict()` existe e é usado em alguns endpoints, mas `GET /tasks` e `GET /users/<id>/tasks` reconstroem o dicionário campo a campo.
**Impacto:** O mesmo recurso tem três formatos de resposta diferentes dependendo da rota que o cliente chamar.

#### [HIGH] Camada de serviço órfã e bloqueante
**File:** `services/notification_service.py:1-48`
**Descrição:** `NotificationService` nunca é importado nem instanciado em lugar nenhum, e `send_email` abre conexão SMTP síncrona — se fosse ligado, bloquearia o ciclo de request.
**Impacto:** A pasta `services/` sugere uma camada de aplicação que não existe, e a única implementação nela está pronta para travar a API quando alguém a plugar.

#### [HIGH] CRUD de categorias dentro do blueprint de relatórios
**File:** `routes/report_routes.py:157-223`
**Descrição:** As quatro rotas de `/categories` vivem em `report_bp`, junto com os relatórios agregados.
**Impacto:** O domínio de categoria não tem dono — quem procurar por ele vai olhar tudo menos o arquivo de relatórios.

### MEDIUM

#### [MEDIUM] API deprecated: `datetime.utcnow()`
**File:** 18 ocorrências — `models/user.py:14` · `models/task.py:15-16, 52` · `utils/helpers.py:38` · `services/notification_service.py:35` · `routes/task_routes.py:31, 72, 215, 285` · `routes/report_routes.py:35, 42, 45, 71, 133`
**Descrição:** `datetime.utcnow()` está deprecated desde o Python 3.12 e devolve um datetime *naive*, sem fuso.
**Impacto:** Comparações com datas vindas do cliente silenciosamente assumem o fuso errado; o substituto é `datetime.now(timezone.utc)`.

#### [MEDIUM] API deprecated: interface legada de query do SQLAlchemy
**File:** 53 ocorrências de `Model.query`, das quais 16 são `.query.get()` — `routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227` · `routes/user_routes.py:29, 94, 136, 155` · `routes/report_routes.py:105, 192, 213`
**Descrição:** `Model.query` e `Query.get()` são a API 1.x do SQLAlchemy, marcada como legada na 2.0 e removida em versão futura.
**Impacto:** O projeto já roda com SQLAlchemy 2.x e depende de camada de compatibilidade; o equivalente moderno é `db.session.get(Model, id)` e `db.session.execute(select(...))`.

#### [MEDIUM] Queries N+1 em três endpoints
**File:** `routes/task_routes.py:41-57` · `routes/report_routes.py:53-68, 157-165`
**Descrição:** `GET /tasks` faz duas queries extras por task para buscar nome de usuário e de categoria — apesar de os `relationship()` já existirem em `models/task.py:20-21`; `summary_report` roda uma query por usuário e `get_categories` uma por categoria.
**Impacto:** 100 tasks geram 201 queries onde dois `joinedload` resolveriam, e o relatório degrada linearmente com a base de usuários.

#### [MEDIUM] `except:` nu engolindo qualquer exceção
**File:** 12 ocorrências — `routes/task_routes.py:62, 137, 204, 236` · `routes/user_routes.py:130, 149` · `routes/report_routes.py:186, 207, 221` · `utils/helpers.py:46, 49, 88`
**Descrição:** Blocos `except:` sem tipo capturam inclusive `KeyboardInterrupt` e `SystemExit`, e vários descartam o erro sem registrar nada.
**Impacto:** `GET /tasks` responde `'Erro interno'` para qualquer falha sem deixar rastro — o bug fica invisível em produção.

#### [MEDIUM] Remoção em cascata feita à mão e categoria deixando órfãos
**File:** `routes/user_routes.py:140-142` · `routes/report_routes.py:211-223` · `models/task.py:13-14, 20-21`
**Descrição:** Deletar usuário percorre as tasks apagando uma a uma em vez de declarar `cascade` no relacionamento, e deletar categoria não trata as tasks que a referenciam.
**Impacto:** Tasks ficam com `category_id` apontando para uma categoria inexistente, e o `GET /tasks` passa a devolver `category_name: null` sem explicação.

#### [MEDIUM] Código morto e constantes centralizadas ignoradas
**File:** `utils/helpers.py:9-116` · `models/task.py:38-48` · `models/user.py:34-38`
**Descrição:** `validate_email`, `sanitize_string`, `generate_id`, `log_action`, `is_valid_color`, `validate_status`, `validate_priority`, `is_admin` e as constantes `VALID_STATUSES`/`MAX_TITLE_LENGTH` aparecem uma única vez no projeto — na própria definição.
**Impacto:** As rotas repetem os literais `['pending', 'in_progress', 'done', 'cancelled']` em cinco lugares enquanto a constante que os define nunca é lida.

#### [MEDIUM] Schema criado no import do módulo, sem migrations
**File:** `app.py:30-31`
**Descrição:** `db.create_all()` roda em tempo de import da aplicação, fora de qualquer comando de CLI.
**Impacto:** Não há versionamento de schema — alterar uma coluna exige apagar o banco, e o efeito colateral dispara em qualquer processo que importe `app`.

#### [MEDIUM] CORS liberado para qualquer origem
**File:** `app.py:15`
**Descrição:** `CORS(app)` sem restringir origens, métodos ou headers.
**Impacto:** Qualquer site chama a API pelo navegador da vítima — e como não há autenticação, não há nada barrando depois.

### LOW

#### [LOW] Listagens sem paginação
**File:** `routes/task_routes.py:14, 247-271` · `routes/user_routes.py:12` · `routes/report_routes.py:30, 53`
**Descrição:** `Task.query.all()` e `User.query.all()` carregam a tabela inteira em memória para depois serializar.
**Impacto:** O tempo de resposta e o uso de memória crescem com a base até o endpoint virar timeout.

#### [LOW] Validação de e-mail frágil e duplicada
**File:** `utils/helpers.py:19-23` (nunca chamada) · `routes/user_routes.py:61, 106`
**Descrição:** A regex não exige TLD, então `a@b` passa, e ela está copiada literalmente em duas rotas enquanto o helper que a encapsula é ignorado.
**Impacto:** Endereços inválidos entram no banco e as notificações por e-mail falham silenciosamente.

#### [LOW] Política de senha de 4 caracteres
**File:** `routes/user_routes.py:64, 115` · `utils/helpers.py:114`
**Descrição:** O mínimo é 4 caracteres, sem exigência de composição.
**Impacto:** Combinado com MD5 sem salt, o espaço de busca é pequeno o bastante para força bruta offline instantânea.

#### [LOW] `if/else` devolvendo booleano literal
**File:** `models/user.py:34-38` · `models/task.py:38-48, 50-60`
**Descrição:** Métodos que retornam `True` num ramo e `False` no outro, incluindo três `if` aninhados em `is_overdue`.
**Impacto:** Esconde uma expressão booleana simples atrás de dez linhas de ramificação.

#### [LOW] `type(x) == list` e imports mortos em massa
**File:** `routes/task_routes.py:7, 141, 210` · `utils/helpers.py:1-7, 103` · `app.py:7` · `routes/user_routes.py:6` · `routes/report_routes.py:7`
**Descrição:** Comparação de tipo por identidade em vez de `isinstance`, e cada arquivo importa módulos que não usa (`json`, `os`, `sys`, `time`, `math`, `hashlib`, `format_date`, `calculate_percentage`).
**Impacto:** `isinstance` quebra com subclasses de `list`, e os imports mortos fazem o leitor procurar dependências que não existem.

#### [LOW] `print` como logging
**File:** `routes/task_routes.py:149, 153, 219, 234` · `routes/user_routes.py:83, 89, 147` · `services/notification_service.py:21, 24` · `utils/helpers.py:39, 41`
**Descrição:** Auditoria e erro saem por `print` em stdout — e `log_action()`, que existe justamente para isso, nunca é chamada.
**Impacto:** Sem nível, sem timestamp estruturado e sem destino configurável, não há como filtrar ou agregar.

### APIs deprecated

Único projeto com APIs deprecated no próprio código-fonte: `datetime.utcnow()` (18 ocorrências) e a interface legada `Model.query` / `Query.get()` do SQLAlchemy (53 ocorrências). Somado ao projeto 2, isso define os três lugares onde o sinal de detecção precisa procurar: **código-fonte, manifesto de dependências e lockfile**.
