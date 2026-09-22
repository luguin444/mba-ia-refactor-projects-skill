================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python 3.13 + Flask 3.0.0 (flask-sqlalchemy 3.1.1, SQLAlchemy 2.0.54)
Files:   15 analyzed | ~1158 lines of code
Date:    2026-09-21

## Summary
CRITICAL: 5 | HIGH: 5 | MEDIUM: 9 | LOW: 6

## Findings

### [CRITICAL] God module — rota acumulando dados, regra e HTTP (AP-06)
**File:** `routes/task_routes.py:1-299`, `routes/report_routes.py:1-223`, `routes/user_routes.py:1-211`
**Description:** Os três arquivos de rota importam `db` e os models diretamente e executam consulta, regra de domínio e montagem de resposta no mesmo handler — 51 chamadas a `.query` nos três somados. São os três maiores arquivos do projeto, quando rota deveria ser a camada mais fina.
**Impact:** Condição CRITICAL aplicável: o mesmo arquivo concentra acesso a dados **e** roteamento HTTP. Nenhuma regra de negócio pode ser testada sem subir o Flask e disparar uma requisição.
**Recommendation:** Extrair repositórios (`repositories/`) e serviços (`services/`) por entidade; a rota passa a delegar e traduzir para HTTP. (→ PB-03)

### [CRITICAL] Senha devolvida no corpo da resposta (AP-04)
**File:** `models/user.py:22` — consumido em `routes/user_routes.py:33, 85, 129, 209`
**Description:** `User.to_dict()` inclui o campo `password` (hash MD5), e quatro rotas devolvem esse dicionário ao cliente: `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e `POST /login`.
**Impact:** Um `GET /users/1` anônimo devolve o hash de senha do usuário; sendo MD5 sem salt, o hash é quebrável por rainbow table em segundos. `GET /users` já omite o campo — as duas rotas do mesmo recurso divergem.
**Recommendation:** Remover `password` do serializer. (→ PB-14 — **exceção de contrato declarada**)

### [CRITICAL] Hash de senha com MD5 (AP-05)
**File:** `models/user.py:29, 32`
**Description:** `set_password()` grava `hashlib.md5(pwd).hexdigest()` e `check_password()` compara o mesmo digest, sem salt nem derivação de chave.
**Impact:** MD5 é quebrado por colisão e por força bruta em GPU. Combinado com o vazamento do hash pelo AP-04 e com a senha mínima de 4 caracteres (`user_routes.py:64`), toda credencial do sistema é recuperável.
**Recommendation:** Trocar por `werkzeug.security.generate_password_hash` / `check_password_hash` (scrypt), já disponível via Flask. (→ PB-05)

### [CRITICAL] Segredos hardcoded (AP-03)
**File:** `app.py:13`, `services/notification_service.py:9-10`
**Description:** `SECRET_KEY = 'super-secret-key-123'` fixa no código versionado, e credencial de SMTP (`taskmanager@gmail.com` / `senha123`) fixa no construtor do serviço de notificação.
**Impact:** Segredo versionado é segredo público — quem clona o repositório assina sessões válidas e autentica no servidor de e-mail. `python-dotenv` já está no `requirements.txt` e nunca foi usado.
**Recommendation:** Mover para variáveis de ambiente lidas em uma camada de config. (→ PB-02)

### [CRITICAL] Debug habilitado em bind público (AP-08)
**File:** `app.py:34`
**Description:** `app.run(debug=True, host='0.0.0.0', port=5000)` — o debugger interativo do Werkzeug é exposto em todas as interfaces de rede.
**Impact:** O console do Werkzeug permite executar Python arbitrário no processo; em rede acessível, é execução remota de código, não inconveniência de log.
**Recommendation:** `debug` e `host` vindos de config por ambiente, com `debug=False` por padrão. (→ PB-02)

### [HIGH] Regra de negócio na camada errada (AP-09)
**File:** `routes/task_routes.py:30-39, 71-80, 96-124, 166-198, 284-287, 296`; `routes/user_routes.py:61-72, 106-121, 171-180`; `routes/report_routes.py:34-37, 59-67, 119-135, 151`
**Description:** Regra "task atrasada", cálculo de `completion_rate`, faixa válida de prioridade, conjunto de status válidos, formato de e-mail e conjunto de roles são decididos dentro dos handlers HTTP.
**Impact:** A definição de "atrasado" está escrita seis vezes; qualquer mudança na regra exige encontrar todas as cópias, e nenhuma delas é testável sem uma requisição HTTP.
**Recommendation:** Mover a decisão para o model (`Task.is_overdue`) e para serviços de domínio; o handler apenas delega. (→ PB-04)

### [HIGH] Camada decorativa — código correto escrito e nunca chamado (AP-14)
**File:** `models/task.py:38-43, 45-48, 50-60`; `models/user.py:34-38`; `utils/helpers.py:19-23, 25-29, 31-34, 36-41, 52-55, 57-108, 110-116`; `services/notification_service.py:1-48`
**Description:** `Task.is_overdue()`, `Task.validate_status()`, `Task.validate_priority()`, `User.is_admin()`, `helpers.process_task_data()`, `helpers.validate_email()`, `helpers.is_valid_color()` e a classe `NotificationService` inteira têm contagem de referência **1** no projeto — só a própria definição — enquanto a lógica equivalente aparece duplicada inline nas rotas. `report_routes.py:7` chega a importar `format_date` e `calculate_percentage` sem nunca usá-los.
**Impact:** Pior que ausência de camada: a estrutura `models/` + `services/` + `utils/` desarma a suspeita de quem lê rápido, enquanto as cópias divergem. `process_task_data()` faz `strip()` no título, as rotas não; `helpers.parse_date()` aceita `DD/MM/YYYY`, as rotas rejeitam.
**Recommendation:** Passar a chamar o símbolo que já existe e apagar a duplicata inline; remover o que sobrar sem uso. (→ PB-15)

### [HIGH] Acesso a dados sem camada própria (AP-13)
**File:** `routes/task_routes.py:2-5, 14, 42, 51, 67, 147-148, 158, 247-266, 275-281`; `routes/user_routes.py:2-4, 12, 29, 67, 81-82, 109, 140, 159, 197`; `routes/report_routes.py:2-5, 15-56, 109, 159-163, 183-184, 192, 205, 213, 218`
**Description:** Os blueprints importam `db` e os models e montam consultas diretamente — `Task.query`, `User.query.get()`, `db.session.add/commit/rollback` dentro dos handlers.
**Impact:** Trocar SQLite por Postgres, adicionar cache ou testar um handler com dados falsos exige tocar em todo arquivo de rota.
**Recommendation:** Introduzir repositórios por entidade; a rota deixa de conhecer `db`. (→ PB-03)

### [HIGH] Erro engolido silenciosamente (AP-15)
**File:** `routes/task_routes.py:62, 137, 204, 236`; `routes/user_routes.py:130, 149`; `routes/report_routes.py:186, 207, 221`; `utils/helpers.py:46, 49, 88`
**Description:** Doze blocos `except:` nus. O de `task_routes.py:62` envolve o handler inteiro de `GET /tasks` e devolve `{'error': 'Erro interno'}` sem registrar nada.
**Impact:** `except:` sem tipo captura também `KeyboardInterrupt` e `SystemExit`. Qualquer falha em `GET /tasks` — inclusive um bug de serialização — vira um 500 opaco sem rastro no log.
**Recommendation:** Capturar exceção específica, registrar via `logging`, e deixar o handler central de erro responder. (→ PB-08)

### [HIGH] Autenticação ausente e token simulado (AP-07)
**File:** `routes/user_routes.py:52, 71-78, 207-211`
**Description:** `POST /login` valida a senha e devolve `'token': 'fake-jwt-token-' + str(user.id)` — string previsível, não assinada e nunca verificada. Nenhuma das 22 rotas lê header de autorização, e `POST /users` aceita `role` do corpo, permitindo cadastro público de administrador.
**Impact:** Qualquer cliente anônimo cria, altera e apaga usuários e tasks de terceiros. `POST /users` com `{"role": "admin"}` concede privilégio administrativo sem verificação.
**Recommendation:** Emitir JWT assinado com a `SECRET_KEY` de ambiente, exigir o header nas rotas de escrita, e ignorar `role` vindo do corpo em cadastro público. **NÃO APLICADO** — ver "Requires Product Decision".

### [MEDIUM] Queries N+1 (AP-17)
**File:** `routes/task_routes.py:42, 51`; `routes/user_routes.py:22`; `routes/report_routes.py:56, 163`
**Description:** `GET /tasks` dispara duas consultas por task (usuário e categoria) dentro do laço, embora `Task.user` e `Task.category` estejam declarados como relacionamento em `models/task.py:20-21`. `GET /reports/summary` consulta as tasks de cada usuário dentro do laço de usuários, e `GET /categories` conta as tasks de cada categoria uma a uma.
**Impact:** Com 500 tasks e 50 usuários, `GET /tasks` faz 1001 consultas e `/reports/summary` faz 50 a mais — latência cresce linearmente com o volume.
**Recommendation:** Usar `joinedload` sobre os relacionamentos já declarados e agregar por `GROUP BY` nos relatórios. (→ PB-06)

### [MEDIUM] APIs deprecated (AP-19)
**File:** `models/task.py:15-16, 52`; `models/user.py:14`; `models/category.py:11`; `routes/task_routes.py:14, 31, 67, 72, 158, 215, 227, 275-285`; `routes/user_routes.py:12, 29, 94, 135, 172`; `routes/report_routes.py:15-56, 133` (+ `utils/helpers.py:38`, `seed.py:11-13`)
**Description:** Duas famílias: `datetime.utcnow()` (21 ocorrências), deprecated no Python 3.12+; e a API legada do SQLAlchemy 1.x — `Model.query` e `Query.get()` (51 ocorrências), substituída na 2.x, com a 2.0.54 instalada.
**Impact:** `utcnow()` devolve datetime ingênuo, fonte silenciosa de erro de fuso; a API legada do SQLAlchemy será removida em versão futura e trava o upgrade.
**Recommendation:** `datetime.now(timezone.utc)` e `db.session.get(Model, id)` / `db.session.execute(select(...))`. (→ PB-11)

### [MEDIUM] Tratamento de erro repetido sem handler central (AP-21)
**File:** `routes/task_routes.py:146-154, 217-223, 231-238`; `routes/user_routes.py:80-90, 127-132, 144-151`; `routes/report_routes.py:182-188, 204-209, 217-223`
**Description:** Nove blocos `try/commit/rollback/return 500` quase idênticos, cada um com a própria mensagem em português. A aplicação não registra nenhum `errorhandler`.
**Impact:** Adicionar um campo à resposta de erro ou trocar o formato exige editar nove funções em três arquivos; um handler novo nasce sem rollback se alguém esquecer de copiar o bloco.
**Recommendation:** Registrar `@app.errorhandler` central e uma exceção de domínio; os handlers deixam de conhecer 500. (→ PB-08)

### [MEDIUM] Duplicação entre handlers irmãos (AP-20)
**File:** `routes/task_routes.py:85-154` vs `156-223`; `routes/user_routes.py:42-90` vs `92-132`; `routes/report_routes.py:167-188` vs `190-209`
**Description:** Criar e atualizar repetem a mesma validação e **já divergiram**: `update_task:167` chama `len(data['title'])` sem checar `None`, enquanto `create_task:92-97` trata título ausente; `create_category:170-171` rejeita corpo vazio e `update_category:196-197` não faz a checagem equivalente; `create_user:64` exige senha com 4 caracteres e `update_user:115` repete o limite por literal solto.
**Impact:** Divergência confirmada por execução: `PUT /tasks/11` com `{"title": null}` devolve **500** onde o irmão `POST /tasks` devolve 400; `POST /categories` com `{}` devolve 400 enquanto `PUT /categories/5` com `{}` devolve **200** sem alterar nada.
**Recommendation:** Extrair a validação para um objeto de entrada único usado pelos dois handlers. (→ PB-12)

### [MEDIUM] Contrato de resposta sem serializer único (AP-22)
**File:** `routes/task_routes.py:17-28` vs `models/task.py:23-36`; `routes/user_routes.py:162-169` vs `models/task.py:23-36`; `routes/user_routes.py:15-23` vs `models/user.py:16-25`; `routes/report_routes.py:138-142`
**Description:** O mesmo recurso é serializado de três formas: `GET /tasks` monta o dicionário campo a campo inline, `GET /tasks/<id>` usa `to_dict()`, e `GET /users/<id>/tasks` monta um subconjunto diferente (sem `user_id`, `category_id`, `updated_at`, `tags`).
**Impact:** Um cliente que lê `tags` de `/tasks` quebra ao ler a mesma task por `/users/<id>/tasks`. Acrescentar um campo exige lembrar de quatro lugares.
**Recommendation:** Serializer único por entidade, com variações explícitas (resumo/completo). `marshmallow` já está declarado no `requirements.txt` e nunca foi usado. (→ PB-12)

### [MEDIUM] Bootstrap acoplado à inicialização (AP-25)
**File:** `app.py:30-31`
**Description:** `with app.app_context(): db.create_all()` roda em tempo de import — qualquer módulo que importe `app` cria o schema como efeito colateral, inclusive `seed.py:2`.
**Impact:** Não há versionamento de schema: uma coluna alterada no model não é migrada, e o banco silenciosamente fica fora de sincronia com o código.
**Recommendation:** Mover a criação para um comando explícito de CLI dentro de uma app factory. (→ PB-18)

### [MEDIUM] CORS irrestrito (AP-26)
**File:** `app.py:15`
**Description:** `CORS(app)` sem restringir origem — equivale a `Access-Control-Allow-Origin: *` em todas as rotas.
**Impact:** Combinado com a ausência de autenticação (AP-07), qualquer página na internet lê e escreve a base pelo navegador da vítima.
**Recommendation:** Lista de origens permitidas vinda de config por ambiente. (→ PB-02)

### [MEDIUM] Limpeza em cascata manual (AP-24)
**File:** `routes/user_routes.py:140-142`; `routes/report_routes.py:211-223`
**Description:** `DELETE /users/<id>` percorre as tasks do usuário e as apaga uma a uma em Python; `DELETE /categories/<id>` não trata as tasks vinculadas de forma alguma.
**Impact:** Apagar um usuário destrói silenciosamente todas as tasks dele — perda de dado não anunciada pelo contrato da rota. Apagar uma categoria deixa tasks apontando para um `category_id` inexistente, e `GET /tasks` passa a devolver `category_name: null` sem erro.
**Recommendation:** Declarar `cascade`/`ondelete` no relacionamento e deixar a decisão de cascata explícita na camada de domínio. (→ PB-17)

### [MEDIUM] Schema sem constraints de integridade (AP-23)
**File:** `models/task.py:13-14`; `models/user.py:11-12`
**Description:** `Task.user_id` e `Task.category_id` são `nullable=True` sem `ondelete`, e o SQLite roda com verificação de chave estrangeira desligada por padrão. `User.password` é `nullable=False` mas nada impede um hash vazio.
**Impact:** Registro órfão entra na base sem erro — o banco aceita uma task apontando para uma categoria que não existe mais, e a aplicação só descobre ao serializar.
**Recommendation:** Declarar `ondelete` nas chaves estrangeiras e habilitar `PRAGMA foreign_keys=ON` na conexão. (→ PB-17)

### [LOW] Código e imports mortos (AP-30)
**File:** `app.py:7`; `routes/task_routes.py:7`; `routes/user_routes.py:6`; `routes/report_routes.py:7-8`; `utils/helpers.py:3-7`; `models/task.py:3`; `requirements.txt:4-6`
**Description:** `os`, `sys`, `json`, `time`, `math` e `hashlib` importados e nunca usados nos arquivos citados; `format_date` e `calculate_percentage` importados em `report_routes.py:7` sem uso. No manifesto, `marshmallow`, `requests` e `python-dotenv` estão declarados e nunca importados por nenhum arquivo do projeto.
**Impact:** Ruído que sugere dependências que não existem e infla a superfície de instalação.
**Recommendation:** Remover imports não usados; decidir entre usar ou remover as três dependências declaradas. (→ PB-21)

### [LOW] Magic numbers e literais repetidos (AP-27)
**File:** `routes/task_routes.py:96, 99, 110, 113, 167, 169, 177, 182`; `routes/user_routes.py:61, 64, 71, 106, 115, 120`; `routes/report_routes.py:24-28, 180`
**Description:** A lista de status válidos aparece 5 vezes, a de roles 3, o regex de e-mail 3, os limites de título (3/200) 4 e o mínimo de senha 2. As prioridades são contadas por cinco consultas separadas em `report_routes.py:24-28`.
**Impact:** **Agrava com AP-14:** as constantes `VALID_STATUSES`, `VALID_ROLES`, `MAX_TITLE_LENGTH`, `MIN_TITLE_LENGTH`, `MIN_PASSWORD_LENGTH` já existem em `utils/helpers.py:110-116` e nenhum handler as usa. Acrescentar um status exige achar cinco literais e lembrar da constante que ninguém lê.
**Recommendation:** Passar a importar as constantes que já existem e apagar os literais. (→ PB-19)

### [LOW] `print` como logging (AP-28)
**File:** `routes/task_routes.py:149, 153, 219, 234`; `routes/user_routes.py:83, 89, 147`; `services/notification_service.py:21, 24`; `utils/helpers.py:39, 41`
**Description:** Onze `print()` usados como auditoria e log de erro, incluindo `print(f"ERRO: {str(e)}")` no caminho de exceção. `helpers.log_action()` é uma função de log própria que só imprime.
**Impact:** Sem nível, sem timestamp estruturado e sem destino configurável — em produção a saída se perde ou polui o stdout do processo.
**Recommendation:** Trocar pelo `logging` da stdlib configurado na camada de config. (→ PB-20)

### [LOW] Ausência de paginação (AP-31)
**File:** `routes/task_routes.py:14, 266, 281`; `routes/user_routes.py:12, 159`; `routes/report_routes.py:30, 53, 159`
**Description:** Oito listagens usam `.all()` e serializam a tabela inteira, sem `limit`, `offset` nem cursor. `GET /reports/summary` carrega todas as tasks e todos os usuários na memória.
**Impact:** Com a base crescendo, `GET /tasks` passa a devolver megabytes e estoura a memória do processo — a própria base semeada tem uma task chamada "Adicionar paginação na API".
**Recommendation:** `limit`/`offset` por query string, com teto padrão. (→ PB-22)

### [LOW] Nomes não descritivos (AP-29)
**File:** `routes/task_routes.py:16-59, 268-269, 283-287`; `routes/user_routes.py:16-24, 37-38, 141-142, 161-181`; `routes/report_routes.py:24-28, 33-43, 55-68, 119-135, 161-164`; `models/task.py:45`; `models/category.py:14`; `seed.py:78-89`
**Description:** Identificadores de uma letra para entidades de negócio — `t` para task, `u` para usuário, `c` para categoria, `p` para prioridade, `d` para o dicionário de resposta, `td` para o registro de seed — e `p1` a `p5` para as contagens por prioridade.
**Impact:** Em laços de 20 linhas como `report_routes.py:119-135`, `t` exige subir até a atribuição para saber o que está sendo iterado.
**Recommendation:** Renomear para o substantivo do domínio. (→ PB-19)

### [LOW] Verbosidade evitável (AP-32)
**File:** `models/task.py:38-43, 45-48, 50-60`; `models/user.py:34-38`; `routes/task_routes.py:141, 210`; `utils/helpers.py:19-23, 52-55, 103`
**Description:** `if cond: return True else: return False` em cinco funções (`validate_status`, `validate_priority`, `is_overdue`, `is_admin`, `validate_email`), e `type(x) == list` em três pontos em vez de `isinstance`.
**Impact:** `is_overdue()` gasta 11 linhas e três níveis de aninhamento para expressar uma conjunção booleana; `type(x) == list` rejeita subclasses de `list`.
**Recommendation:** Retornar a expressão diretamente e usar `isinstance`. (→ PB-19)

## Contract Exceptions
- `models/user.py:22` — campo `password` removido de `User.to_dict()` (AP-04). Afeta o corpo de `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e `POST /login`; o restante do objeto fica intacto. A correção **converge** o contrato: `GET /users` (`user_routes.py:15-23`) já omitia o campo.

Nenhuma outra. Nenhum endpoint será removido — não há rota que exista apenas como vulnerabilidade, e nenhum log grava credencial.

## Requires Product Decision
- **AP-07 — Autenticação ausente e token simulado** (`routes/user_routes.py:52, 71-78, 207-211`). A transformação seria: emitir JWT assinado com a `SECRET_KEY` vinda de ambiente, exigir `Authorization` nas rotas de escrita e ignorar `role` vindo do corpo em cadastro público. **Não aplicada** porque passaria as 20 rotas não públicas a responder 401 sem token — quebra total do contrato HTTP que a Fase 3 se compromete a preservar. A decisão de introduzir autenticação, e de como migrar os clientes existentes, é de produto.
- Consequência aceita enquanto isso: `POST /users` com `{"role": "admin"}` continua concedendo privilégio administrativo a qualquer anônimo. O AP-05 (troca de MD5 por scrypt) **será** aplicado e reduz o impacto do vazamento, mas não fecha esta porta.

================================
Total: 25 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
