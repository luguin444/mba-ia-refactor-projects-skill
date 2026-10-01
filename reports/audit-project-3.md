================================
ARCHITECTURE AUDIT REPORT
================================
Project:      task-manager-api
Stack:        Python 3.13.13 (.venv) + Flask 3.0.0 (flask==3.0.0) + Flask-SQLAlchemy 3.1.1 (SQLAlchemy 2.1.1 instalado)
Dependencies: flask-cors 4.0.0, marshmallow 3.20.1 (declarada, nunca importada), requests 2.31.0 (declarada, nunca importada), python-dotenv 1.0.0 (declarada, nunca importada)
Domain:       Gerenciador de tarefas: usuários, categorias e tasks com status, prioridade, prazo e relatórios de produtividade
Architecture: Camadas decorativas: models/ e routes/ existem, mas Task.is_overdue/validate_status/validate_priority e utils.process_task_data nunca são chamados; a regra (atraso, validação) está duplicada inline nas rotas, que são os maiores arquivos (299/223/211 linhas)
Files:        15 analyzed | ~1158 lines of code
Routes:       22 endpoints
DB tables:    users, categories, tasks (SQLite, sqlite:///tasks.db → instance/tasks.db)
Date:         2026-09-30

## Summary
CRITICAL: 8 | HIGH: 4 | MEDIUM: 8 | LOW: 6

## Findings

### [CRITICAL] Autenticação ausente ou simulada (AP-07)
**File:** `routes/user_routes.py:207-211` (login), `routes/user_routes.py:10, 27, 92, 134, 153`, `routes/task_routes.py:11, 65, 85, 156, 225, 240, 273`, `routes/report_routes.py:12, 103, 157, 167, 190, 211`
**Description:** Nenhuma rota lê o header `Authorization`, e o login devolve `'fake-jwt-token-' + str(user.id)`, um token previsível e sem assinatura. Condição CRITICAL: rotas anônimas devolvem dado de terceiros (`GET /users` lista nome e e-mail de todos) e permitem escrita destrutiva (`DELETE /users/<id>`, `DELETE /categories/<id>`).
**Impact:** Qualquer pessoa na rede lê os e-mails de todos os usuários, apaga contas e tasks alheias, e "forja" o token de qualquer id trocando o número no final da string.
**Recommendation:** O login passa a emitir um JWT HS256 assinado com `SECRET_KEY` vindo do ambiente, com `exp` de 12h e `sub`/`role` no payload (PyJWT, dependência nova). A verificação fica em `middlewares/`, com três níveis: credencial, dono-ou-admin e admin. O escopo vai rota por rota em "Contract Exceptions". Respostas: anônimo ou token inválido recebe 401 `{"error": ...}`; autenticado sem permissão recebe 403 `{"error": ...}`. (→ PB-24, exceção de contrato declarada)

### [CRITICAL] Privilégio atribuído por entrada do cliente (AP-34)
**File:** `routes/user_routes.py:52, 71-72, 78` (POST /users), `routes/user_routes.py:119-125` (PUT /users/<id>: `role` e `active`)
**Description:** O cadastro público lê `role` do corpo, confere se está na lista `['user', 'admin', 'manager']` (que inclui `admin`) e grava. Confirmado por execução: `POST /users` anônimo com `"role": "admin"` → 201, registro gravado com `role: "admin"`.
**Impact:** Um único campo a mais no JSON do cadastro dá a qualquer pessoa um perfil administrativo, sem precisar de outra falha.
**Recommendation:** `POST /users` passa a **ignorar** o campo `role` (não rejeita a requisição) e grava sempre o default do servidor, `user`, definido como constante de domínio. Em `PUT /users/<id>`, `role` e `active` só são aplicados quando quem pede é admin. Para dono não-admin os dois campos são ignorados, e o resto da atualização segue igual. (→ PB-25, exceção de contrato declarada)

### [CRITICAL] Dado sensível na resposta (AP-04)
**File:** `models/user.py:21` (exposto por `routes/user_routes.py:33, 85, 129, 209`)
**Description:** `User.to_dict()` inclui o campo `password` (hash MD5). Por isso `POST /users`, `GET /users/<id>`, `PUT /users/<id>` e `POST /login` devolvem o hash no corpo, como confirmado por execução.
**Impact:** Um `GET /users/<id>` anônimo entrega o MD5 sem salt da senha de qualquer usuário, que é revertido por tabela pública em segundos.
**Recommendation:** Remover apenas o campo `password` de `User.to_dict()`, mantendo o resto do objeto idêntico. (→ PB-14, exceção de contrato declarada)

### [CRITICAL] Hash de senha obsoleto (AP-05)
**File:** `models/user.py:29, 32`
**Description:** A senha é gravada como `hashlib.md5(pwd.encode()).hexdigest()`, uma função de propósito geral sem salt e sem derivação.
**Impact:** Somado ao AP-04, todo hash vazado é revertido por rainbow table, e duas pessoas com a mesma senha têm o mesmo hash.
**Recommendation:** `set_password`/`check_password` passam a usar `werkzeug.security.generate_password_hash`/`check_password_hash` (scrypt com salt). O projeto é seed-only, então não haverá caminho legado de MD5. O banco local existente (`instance/tasks.db`, semeado com MD5) precisa ser re-semeado com `python seed.py`, e é isso que a Fase 3 faz. (→ PB-05)

### [CRITICAL] Segredo hardcoded (AP-03)
**File:** `app.py:13`, `services/notification_service.py:9-10`
**Description:** `SECRET_KEY = 'super-secret-key-123'` está fixo no código, e o usuário e a senha SMTP (`taskmanager@gmail.com` / `senha123`) estão literais no construtor do `NotificationService`.
**Impact:** Com o AP-07 corrigido, a `SECRET_KEY` vira a chave de assinatura dos tokens: mantida no código, qualquer leitor do repositório forjaria tokens de admin.
**Recommendation:** Criar um módulo de config que lê `SECRET_KEY` do ambiente (`python-dotenv` + `.env.example` versionado sem valores + `.env` no `.gitignore`). Sem a variável, ele gera uma chave efêmera e emite um **warning** no log, o que significa que os tokens são invalidados a cada restart. A credencial SMTP sai junto com o `NotificationService`, que é código morto (ver AP-30). (→ PB-02)

### [CRITICAL] Modo debug habilitado em bind público (AP-08)
**File:** `app.py:34`
**Description:** `app.run(debug=True, host='0.0.0.0', port=5000)` liga o debugger do Werkzeug escutando em todas as interfaces.
**Impact:** O console interativo do Werkzeug exposto na rede dá execução remota de código a quem alcança a porta 5000.
**Recommendation:** `DEBUG`, `HOST` e `PORT` passam a vir da config, com defaults `false`, `127.0.0.1` e `5000`. Para expor na rede, é preciso definir `HOST=0.0.0.0` explicitamente. (→ PB-02)

### [CRITICAL] Dependências com CVE e APIs deprecated (AP-19)
**File:** `requirements.txt:1-6`, `app.py:15`. `datetime.utcnow()`: `models/task.py:15-16, 52`, `models/category.py:11`, `models/user.py:14`, `routes/task_routes.py:31, 72, 215, 285`, `routes/user_routes.py:172`, `routes/report_routes.py:35, 42, 45, 71, 133`, `utils/helpers.py:38`, `seed.py:66-74`. `Query.get()`: `routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227`, `routes/user_routes.py:29, 94, 136, 155`, `routes/report_routes.py:105, 192, 213`
**Description:** `flask-cors==4.0.0` tem CVE-2024-6866, CVE-2024-6839 e CVE-2024-6844 (casamento de origem e caminho inconsistente), além de CVE-2024-6221 e CVE-2024-1681. O projeto usa o mesmo mecanismo de forma permissiva (`CORS(app)` para todas as origens), e é isso que torna o finding CRITICAL. Também têm CVE: `flask==3.0.0` (CVE-2026-27205; `session` não é usada, então não é explorável aqui), `requests==2.31.0` (CVE-2024-47081, CVE-2024-35195, CVE-2026-25645), `marshmallow==3.20.1` (CVE-2025-68480) e `python-dotenv==1.0.0` (CVE-2026-28684). O boot emite `DeprecationWarning` de `utcnow()` e `LegacyAPIWarning` de `Query.get()`.
**Impact:** Os CVEs de matching do flask-cors se somam ao CORS aberto, e três pacotes vulneráveis são instalados sem nunca serem importados.
**Recommendation:**
- `flask` 3.0.0→3.1.3, `flask-cors` 4.0.0→6.0.5 e `python-dotenv` 1.0.0→1.2.3 (passa a ser usado pela config); as três versões estão limpas no OSV.
- Remover `marshmallow` e `requests`, que nunca são importados.
- Adicionar `pyjwt==2.15.1` (OSV limpo).
- Trocar `utcnow()` por um helper timezone-aware que devolve UTC *naive*, para que o `str()` das datas continue idêntico no contrato.
- Trocar `Query.get()` por `db.session.get()`, e `Model.query` por `select()` nos repositórios.

(→ PB-11)

### [CRITICAL] God modules: rotas com acesso a dados e HTTP (AP-06)
**File:** `routes/task_routes.py:1-299`, `routes/user_routes.py:1-211`, `routes/report_routes.py:1-223`
**Description:** Cada arquivo de rota faz query (`Task.query`, `db.session`), decide regra (atraso, validação, cascata, taxa de conclusão) e trata HTTP, e os três são os maiores arquivos do projeto. Condição CRITICAL: acesso a dados e roteamento estão no mesmo arquivo. `report_routes.py` também hospeda o CRUD de categorias (linhas 157-223), um segundo domínio.
**Impact:** Nenhuma regra pode ser testada sem subir HTTP e banco, e cada mudança de regra toca o mesmo arquivo que registra rotas e faz queries.
**Recommendation:** Separar por domínio (tasks, users, reports, categories), e o CRUD de categorias sai de `report_routes.py` para um módulo próprio.
- Rotas: só registram e delegam.
- Controllers: leem request e montam response.
- Regras: vão para `services/` (que hoje só contém código morto).
- Queries: vão para repositórios.
- Models: mantêm entidade, serialização e a regra de entidade que já existe (`is_overdue`, ver AP-14).

(→ PB-03)

### [HIGH] Camada decorativa (AP-14)
**File:** `models/task.py:38-43, 45-48, 50-60`, `utils/helpers.py:14-17, 19-23, 57-108, 110-116`. Duplicado em `routes/task_routes.py:30-39, 71-80, 110, 113, 177, 182, 284-287, 296`, `routes/user_routes.py:61, 71, 106, 120, 171-180`, `routes/report_routes.py:34-36, 67, 133-135, 151`
**Description:** `Task.is_overdue`, `Task.validate_status`, `Task.validate_priority`, `validate_email` e `process_task_data` têm contagem de referências 1 (nunca chamados). As constantes `VALID_STATUSES`/`VALID_ROLES`/`MIN_TITLE_LENGTH` etc. também. `calculate_percentage` é importado e nunca usado. A mesma lógica está copiada inline nas rotas: a condição de atraso aparece seis vezes, e `round((x / total) * 100, 2) if total > 0 else 0` três.
**Impact:** A estrutura sugere que a regra mora no model e nos helpers, mas quem altera `is_overdue` não muda nada no comportamento, e as seis cópias podem divergir sem ninguém perceber.
**Recommendation:** Os services passam a chamar o que já existe: `Task.is_overdue()`, `validate_status`/`validate_priority`, `validate_email`, `calculate_percentage` e as constantes de domínio. **Exceção declarada:** `process_task_data` **não** será chamado, e sim removido, porque já divergiu das rotas. Ele faz `strip()` no título, aceita prioridade `"2"` como string via `int()`, aceita data `dd/mm/YYYY` e usa outras mensagens (`'Título deve ter entre 3 e 200 caracteres'`). Usá-lo mudaria o contrato de `POST`/`PUT /tasks`. A validação única fica no service, com a semântica atual das rotas. (→ PB-15)

### [HIGH] Regra de negócio na camada HTTP (AP-09)
**File:** `routes/task_routes.py:30-39, 92-124, 166-213, 275-297`, `routes/user_routes.py:54-72, 102-125, 140-142, 171-180`, `routes/report_routes.py:15-99, 111-153`
**Description:** Os handlers HTTP decidem atraso, validam domínio (título, status, prioridade, e-mail, senha, papel), escolhem cascata na remoção e calculam estatísticas e taxas de conclusão.
**Impact:** A mesma regra aplicada fora do HTTP (seed, job, CLI) teria de ser reescrita, e não há como testá-la sem request.
**Recommendation:** Mover a regra para services por domínio (`TaskService`, `UserService`, `CategoryService`, `ReportService`) e a regra de entidade para o model. Os controllers só traduzem request→chamada→response. (→ PB-04)

### [HIGH] Acesso a dados sem camada própria (AP-13)
**File:** `routes/task_routes.py:2-5`, `routes/user_routes.py:2-4`, `routes/report_routes.py:2-5`
**Description:** Os três módulos de rota importam `db` e os models e montam queries (`Task.query.filter_by(...)`, `db.session.add/commit/delete`) dentro do handler.
**Impact:** Trocar a forma de consulta (eager loading, paginação, outro banco) exige editar cada handler HTTP.
**Recommendation:** Criar repositórios (`TaskRepository`, `UserRepository`, `CategoryRepository`) como único ponto que fala com `db.session`. Commit e rollback ficam numa unidade de trabalho única, chamada pelo service. (→ PB-03)

### [HIGH] Erro engolido silenciosamente (AP-15)
**File:** `routes/task_routes.py:62, 137, 204, 236`, `routes/user_routes.py:130, 149`, `routes/report_routes.py:186, 207, 221`, `utils/helpers.py:46, 49, 88`
**Description:** Há doze `except:` nus que não registram nada. Em `GET /tasks` (`task_routes.py:62-63`), qualquer falha vira `{'error': 'Erro interno'}` sem log nenhum.
**Impact:** Uma falha real de banco em produção some sem rastro, e `except:` nu também captura `KeyboardInterrupt`/`SystemExit`.
**Recommendation:**
- Parse de data: `except (ValueError, TypeError)`, mantendo o 400 com a mesma mensagem.
- Falha de commit: `except SQLAlchemyError` com rollback e log, mantendo as mensagens atuais (`'Erro ao criar task'`, `'Erro ao atualizar'`, `'Erro ao deletar'`, `'Erro ao criar usuário'`, `'Erro ao criar categoria'`).
- O `except` genérico de `GET /tasks` sai, e o handler central (AP-21) devolve o mesmo corpo `{'error': 'Erro interno'}` com log.
- Os `except` de `helpers.py` saem junto com o código morto.

(→ PB-08)

### [MEDIUM] Queries N+1 (AP-17)
**File:** `routes/task_routes.py:42, 51`, `routes/user_routes.py:22`, `routes/report_routes.py:56, 163`
**Description:** `GET /tasks` faz `User.query.get` e `Category.query.get` por task, ignorando os relacionamentos `Task.user`/`Task.category` já declarados (1 + 2N). As demais ocorrências seguem o mesmo padrão: `GET /users` faz lazy-load de `u.tasks` por usuário, `GET /reports/summary` uma query por usuário, e `GET /categories` um `count()` por categoria.
**Impact:** O número de queries cresce linearmente com o tamanho das tabelas em toda listagem.
**Recommendation:** Usar eager loading (`joinedload`/`selectinload`) dos relacionamentos já declarados e contagens agregadas com `GROUP BY` no repositório. Os corpos de resposta continuam idênticos. (→ PB-06)

### [MEDIUM] Contrato de resposta sem serializer único (AP-22)
**File:** Task: `models/task.py:23-36`, `routes/task_routes.py:17-28`, `routes/user_routes.py:162-169`, `routes/report_routes.py:38-43`. User: `models/user.py:16-25`, `routes/user_routes.py:15-23`, `routes/report_routes.py:63-68, 138-142`
**Description:** Task é montada campo a campo em quatro lugares, com conjuntos de campos diferentes, e User em três. `GET /tasks` ignora `Task.to_dict()` e reconstrói o mesmo dicionário à mão.
**Impact:** Um campo novo ou renomeado em Task precisa ser lembrado em quatro arquivos, e as formas já divergem por rota.
**Recommendation:** Partir de `to_dict()` como base e definir as variantes por rota num único lugar: lista com `overdue`/`user_name`/`category_name`, subconjunto de `/users/<id>/tasks` e item de atrasadas. Cada variante preserva exatamente o conjunto de campos que a rota devolve hoje. (→ PB-12)

### [MEDIUM] Duplicação entre handlers irmãos (AP-20)
**File:** `routes/task_routes.py:92-144` × `166-213`, `routes/user_routes.py:54-78` × `102-125`
**Description:** A validação de criar e atualizar está copiada, e as cópias já divergiram:
- Título vazio: `POST /tasks` responde `'Título é obrigatório'` e `PUT` responde `'Título muito curto'`.
- Data inválida: o POST diz `'... Use YYYY-MM-DD'` e o PUT não.
- Senha curta: o POST responde `'Senha deve ter no mínimo 4 caracteres'` e o PUT `'Senha muito curta'`.
- Nome vazio: o PUT de usuário aceita, o POST não.
**Impact:** A regra muda num handler e esquece o outro. As divergências acima já são essa falha.
**Recommendation:** Uma função de validação compartilhada no service, parametrizada por operação, **preservando** a mensagem atual de cada uma. Harmonizar as mensagens seria mudança de contrato não declarada, por isso as divergências ficam documentadas no código e não são alteradas. (→ PB-12)

### [MEDIUM] Tratamento de erro repetido sem handler central (AP-21)
**File:** `routes/task_routes.py:146-154, 217-223, 231-238`, `routes/user_routes.py:80-90, 127-132, 144-151`, `routes/report_routes.py:182-188, 204-209, 217-223`
**Description:** O mesmo bloco `try/commit/except/rollback/return 500` se repete em nove handlers, e não há `errorhandler` registrado. Entradas com tipo errado (`priority: "2"` ou `title: 123` em `POST /tasks`, `?priority=abc` em `/tasks/search`) derrubam o handler e devolvem a página HTML 500 do Werkzeug, como confirmado por execução.
**Impact:** Os erros respondem em formatos diferentes (JSON ou HTML), e cada handler novo precisa lembrar do rollback.
**Recommendation:** Exceções de domínio (`ValidationError` 400, `NotFoundError` 404, `ConflictError` 409, `UnauthorizedError` 401, `ForbiddenError` 403) e um middleware de erro central.
- Exceção não tratada: vira 500 `{"error": "Erro interno"}` com log.
- `HTTPException` do Werkzeug (415 sem JSON, 400 de JSON malformado, 404 de rota inexistente, 405) passa intacta, em HTML como hoje.
- **Divergência de conserto de bug declarada:** em toda rota cujo handler levanta exceção não tratada, o status continua 500, mas o corpo passa de página HTML para JSON `{"error": "Erro interno"}`. Será apresentada na verificação com os dois valores.

(→ PB-08)

### [MEDIUM] Limpeza em cascata manual (AP-24)
**File:** `routes/user_routes.py:140-142`
**Description:** `DELETE /users/<id>` percorre as tasks do usuário com `for t in tasks: db.session.delete(t)` antes de apagar o usuário.
**Impact:** Qualquer outro caminho que apague usuário (seed, admin, script) deixa tasks órfãs, porque a regra de cascata mora no handler.
**Recommendation:** Declarar `cascade="all, delete-orphan"` no relacionamento User→Task e remover o laço. O resultado é o mesmo: usuário e tasks apagados numa transação. (→ PB-17)

### [MEDIUM] Schema sem constraints de integridade aplicadas (AP-23)
**File:** `models/task.py:13-14`, `database.py:3`
**Description:** `tasks.user_id` e `tasks.category_id` declaram `ForeignKey`, mas o SQLite só aplica FK com `PRAGMA foreign_keys = ON` por conexão, e nada liga a pragma. As constraints são decorativas.
**Impact:** Qualquer escrita fora das rotas que validam existência (seed, script, rota futura) grava task apontando para usuário ou categoria inexistente.
**Recommendation:** Ligar `PRAGMA foreign_keys=ON` em cada conexão via evento `connect` do engine. Verificado que não muda o contrato: a remoção de usuário apaga as tasks antes, a de categoria anula o FK antes (comportamento atual do ORM), e a criação já valida existência. (→ PB-17)

### [MEDIUM] Bootstrap acoplado à importação (AP-25)
**File:** `app.py:30-31`
**Description:** `db.create_all()` roda em tempo de import do módulo `app`, ou seja, qualquer `import app` (inclusive o do `seed.py`) cria o schema.
**Impact:** Importar a aplicação para teste ou script tem efeito colateral no banco configurado.
**Recommendation:** Criar um factory `create_app()` que inicializa o schema por chamada explícita (`init_db`) no boot do entry point. O seed continua sendo comando explícito (`python seed.py`). (→ PB-18)

### [MEDIUM] CORS irrestrito (AP-26)
**File:** `app.py:15`
**Description:** `CORS(app)` libera todas as origens em todas as rotas.
**Impact:** Qualquer site pode chamar a API a partir do navegador da vítima e ler a resposta.
**Recommendation:** As origens passam a vir de `CORS_ORIGINS` na config. O default `*` preserva o comportamento atual e o contrato. **Quais origens liberar é decisão de produto** (ver "Requires Product Decision"). O componente vulnerável do risco (os CVEs do flask-cors) é corrigido no AP-19. (→ PB-02)

### [LOW] Código e imports mortos (AP-30)
**File:**
- Código morto (contagem 1): `services/notification_service.py:1-48` (`NotificationService` nunca instanciado), `models/user.py:34-38` (`is_admin`), `utils/helpers.py:9-12, 25-29, 31-34, 36-41, 43-50, 52-55` (`format_date`, `sanitize_string`, `generate_id`, `log_action`, `parse_date`, `is_valid_color`).
- Imports não usados: `app.py:7`, `routes/task_routes.py:7`, `routes/user_routes.py:6`, `routes/report_routes.py:7-8`, `utils/helpers.py:3-7`, `models/task.py:3`.
- Dependências nunca importadas: `requirements.txt:4-5`.
**Description:** Há funções, uma classe de serviço inteira e imports que ninguém referencia. `parse_date` só é usado por `process_task_data`, que também está morto (AP-14).
**Impact:** O código morto engana quem lê sobre o que o sistema faz (parece haver notificação por e-mail e não há) e carrega um segredo hardcoded (AP-03).
**Recommendation:** Remover tudo o que foi listado. O `NotificationService` sai inteiro, e se a notificação vier a ser ligada, a credencial SMTP virá da config. (→ PB-21)

### [LOW] Magic numbers e literais repetidos (AP-27)
**File:** `models/task.py:39`, `routes/task_routes.py:96, 99, 110, 113, 167, 169, 177, 182`, `routes/user_routes.py:64, 71, 115, 120`, `utils/helpers.py:75`, `models/category.py:10`, `routes/report_routes.py:180`
**Description:** A lista de status válidos aparece literal em quatro lugares e a de papéis em dois, e os limites de título (3/200), senha (4) e prioridade (1/5) e a cor default `#000000` estão cravados na lógica. As constantes equivalentes existem em `utils/helpers.py:110-116` e são ignoradas.
**Impact:** Um status novo precisa ser lembrado em quatro arquivos.
**Recommendation:** Um único módulo de constantes de domínio, usado por model e service, e os literais repetidos saem. (→ PB-19)

### [LOW] `print` como logging (AP-28)
**File:** `routes/task_routes.py:149, 153, 219, 234`, `routes/user_routes.py:83, 89, 147`, `services/notification_service.py:21, 24`, `utils/helpers.py:39, 41`
**Description:** A auditoria de criação e remoção e os erros de commit saem por `print`, sem nível nem destino configurável.
**Impact:** Os erros de banco ficam misturados na stdout, sem nível para filtrar nem alertar.
**Recommendation:** Usar `logging` com logger por módulo, configurado na inicialização. As mensagens de auditoria viram `info` e os erros viram `error`/`exception`. Os `print` de `seed.py` permanecem, porque são a saída de um comando de CLI para quem o executa. (→ PB-20)

### [LOW] Verbosidade evitável (AP-32)
**File:** `models/task.py:38-60`, `models/user.py:34-38`, `routes/task_routes.py:30-39, 41-57, 141, 210`, `utils/helpers.py:21-23, 53-55, 103`
**Description:** Há `if cond: return True else: return False`, pirâmides de `if` aninhados de 3 níveis para uma condição booleana e `type(x) == list` em vez de `isinstance`.
**Impact:** Dez linhas para uma condição de uma linha escondem a regra e facilitam divergência entre cópias.
**Recommendation:** Retornar a expressão booleana diretamente, achatar as condições e usar `isinstance`. (→ PB-19)

### [LOW] Nomes não descritivos (AP-29)
**File:** `routes/report_routes.py:24-28` (`p1`…`p5`), `routes/task_routes.py:16, 51`, `routes/user_routes.py:14`, `routes/report_routes.py:55, 160` (`t`, `u`, `c`, `cat` para entidades), `models/category.py:14` (`d`)
**Description:** As contagens por prioridade se chamam `p1`…`p5`, e as entidades de negócio são nomeadas com uma letra.
**Impact:** É preciso ler o dicionário final para saber que `p1` significa prioridade "critical".
**Recommendation:** Nomes de domínio (`task`, `user`, `category`, contagem por prioridade num mapa nomeado) no código reescrito. (→ PB-19)

### [LOW] Ausência de paginação (AP-31)
**File:** `routes/task_routes.py:14, 266`, `routes/user_routes.py:12`, `routes/report_routes.py:159`
**Description:** `GET /tasks`, `GET /tasks/search`, `GET /users` e `GET /categories` carregam a tabela inteira com `.all()`, sem limite.
**Impact:** O tempo de resposta e a memória crescem com a tabela inteira a cada chamada.
**Recommendation:**
- Aceitar `limit`/`offset` **opcionais** nessas quatro rotas, com `ORDER BY id`. Valor não inteiro ou negativo responde 400 JSON.
- Sem os parâmetros, a rota devolve a lista inteira como hoje, o que preserva o contrato.
- O tamanho de página default (forçar paginação) é **decisão de produto**.

(→ PB-22)

## Contract Exceptions

- `models/user.py:21`: campo `password` removido de `User.to_dict()` (AP-04). Mudam de forma: `POST /users` (201), `GET /users/<id>`, `PUT /users/<id>` e o objeto `user` de `POST /login`. `GET /users` não muda, porque nunca incluiu o campo.
- `routes/user_routes.py:210`: em `POST /login`, o valor de `token` deixa de ser `fake-jwt-token-<id>` e passa a ser um JWT HS256 assinado, com `exp` de 12h (AP-07). O nome do campo e o resto do corpo se mantêm, exceto `password` (item acima).
- `routes/user_routes.py:52, 71-72, 78`: `POST /users` passa a ignorar `role` e grava sempre `user` (AP-34). Quem enviava `"role": "admin"`/`"manager"` recebe 201 com `"role": "user"`, e quem enviava um papel inválido recebe 201 em vez de 400 `'Role inválido'`.
- `routes/user_routes.py:119-125`: em `PUT /users/<id>` por dono não-admin, `role` e `active` são ignorados (AP-34), incluindo valor de papel inválido, que deixa de dar 400. Admin continua alterando os dois, com a mesma validação.
- Rotas que passam a exigir credencial (AP-07). Anônimo ou token inválido: 200/201/404 → **401**. Autenticado sem o nível exigido → **403**. Autenticado com o nível exigido recebe exatamente o que recebia antes.
    `GET    /users                  admin            lista nome, e-mail e papel de todos os usuários`
    `GET    /users/<id>             dono ou admin    e-mail e tasks de outro usuário`
    `PUT    /users/<id>             dono ou admin    edita outro usuário; role/active só admin aplica`
    `DELETE /users/<id>             dono ou admin    apaga a conta e as tasks de outro usuário`
    `GET    /users/<id>/tasks       dono ou admin    tasks de outro usuário`
    `GET    /reports/summary        admin            relatório agregado nomeando cada usuário`
    `GET    /reports/user/<id>      dono ou admin    relatório pessoal com e-mail`
    `GET    /tasks                  credencial       quadro compartilhado da equipe, não de um sujeito`
    `GET    /tasks/<id>             credencial       mesmo dado já exposto no quadro da equipe (GET /tasks); dono-ou-admin aqui não protegeria nada`
    `GET    /tasks/search           credencial       filtro sobre o quadro da equipe`
    `GET    /tasks/stats            credencial       agregado do quadro da equipe`
    `POST   /tasks                  credencial       cria item que nasce com coluna de dono (user_id)`
    `PUT    /tasks/<id>             dono ou admin    dono = tasks.user_id; task sem responsável só admin edita`
    `DELETE /tasks/<id>             dono ou admin    dono = tasks.user_id; task sem responsável só admin apaga`
    `POST   /categories             admin            escrita em dado sem dono, com cadastro público`
    `PUT    /categories/<id>        admin            escrita em dado sem dono, com cadastro público`
    `DELETE /categories/<id>        admin            apaga dado sem dono, com cadastro público`
  Permanecem públicas, deliberadamente:
    `GET    /                       público          raiz, metadado estático da API`
    `GET    /health                 público          liveness, sem dado de usuário`
    `POST   /login                  público          emite a credencial`
    `POST   /users                  público          cadastro: único caminho de entrada do usuário no sistema (role ignorado, ver acima)`
    `GET    /categories             público          catálogo compartilhado sem dado pessoal`
  Ordem das checagens: em rotas com id de usuário no caminho, a autorização vem antes da busca (não-admin em `/users/999` → 403; admin → 404). Em `PUT`/`DELETE /tasks/<id>`, a task é buscada primeiro, porque é ela que diz quem é o dono (inexistente → 404, de outro → 403). Para o anônimo, o 401 precede qualquer outra validação, inclusive o 415 de corpo sem JSON.
- Divergência de conserto de bug (não é exceção de contrato; é declarada aqui e será apresentada na verificação com os dois valores): toda exceção não tratada em qualquer handler mantém o status 500, mas o corpo passa de página HTML do Werkzeug para JSON `{"error": "Erro interno"}` (AP-21). Gatilhos conhecidos:
  - `POST /tasks` e `PUT /tasks/<id>` com `priority` não numérico ou `title` não string;
  - `GET /tasks/search` com `priority` ou `user_id` não inteiro;
  - `POST /users` e `PUT /users/<id>` com `email`/`password` não string.
- Rotas de listagem (AP-31): os parâmetros novos `limit`/`offset` são opt-in, e sem eles a resposta é idêntica.

## Requires Product Decision

- **AP-26: quais origens o CORS deve liberar.** A Fase 3 torna a lista configurável por `CORS_ORIGINS`, com default `*` (comportamento atual), mas não escolhe as origens.
- **AP-31: tamanho de página default.** A Fase 3 implementa `limit`/`offset` opcionais, mas forçar paginação por padrão (e com qual tamanho) muda o contrato das listagens e depende de quem consome a API.

================================
Total: 26 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
