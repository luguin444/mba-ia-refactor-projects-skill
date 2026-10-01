# refactor-arch — Refatoração Arquitetural Automatizada

Skill do Claude Code que audita e refatora um projeto legado para MVC em três fases: **análise** de stack e arquitetura, **auditoria** com relatório por severidade, e **refatoração** validada por diff de contrato HTTP.

Executada nos três projetos do desafio — dois Python/Flask com níveis de organização opostos e um Node.js/Express. Os três passaram nos quatro critérios de aceite.

| Artefato | Onde |
|---|---|
| Skill | [`code-smells-project/.claude/skills/refactor-arch/`](code-smells-project/.claude/skills/refactor-arch/) (cópia canônica, replicada nos outros dois) |
| Relatórios de auditoria | [`reports/audit-project-1.md`](reports/audit-project-1.md) · [`-2`](reports/audit-project-2.md) · [`-3`](reports/audit-project-3.md) |
| Análise manual completa | [`analise-manual.md`](analise-manual.md) — 76 findings |
| Documento de design | [`docs/design.md`](docs/design.md) |
| Enunciado original | [`docs/desafio.md`](docs/desafio.md) |

### Reentrega — o que mudou depois do feedback

O feedback apontou que os três relatórios marcavam o AP-07 (autenticação ausente) e o deixavam sem aplicar, que no `task-manager-api` o `POST /users` ainda aceitava `role` do corpo e que o login seguia devolvendo `fake-jwt-token`. A correção foi feita **na skill**, não à mão nos projetos, e os três projetos foram reexecutados do zero a partir do boilerplate:

| Mudança na skill | Onde |
|---|---|
| Regra 8: **todo finding CRITICAL e HIGH é corrigido**, inclusive autenticação e escalonamento de privilégio; `REQUER DECISÃO DE PRODUTO` fica restrito ao que não é dedutível do código (ex.: qual gateway contratar) | `SKILL.md` |
| PB-24: autenticação vira transformação aplicada — token assinado com segredo do ambiente e expiração, middleware com três níveis (`credencial`, `dono ou admin`, `admin`) e classificação **rota por rota** no relatório | `refactoring-playbook.md` |
| AP-34 + PB-25: **privilégio vindo do cliente** (ex.: `role` no cadastro público) é CRITICAL; o papel passa a ser default do servidor | `antipattern-catalog.md`, `refactoring-playbook.md` |
| Com cadastro público, escrita em dado **sem dono** (catálogo, categorias) exige **admin** — "credencial" custa uma requisição | `refactoring-playbook.md` (PB-24) |
| Regra 9: relatório anterior é histórico, não instrução — a skill não herda escopo nem decisão de uma execução descartada | `SKILL.md`, `report-template.md` |

Resultado: os três projetos emitem JWT assinado, protegem cada rota com o nível declarado no relatório (anônimo → 401, sem permissão → 403) e nenhum finding CRITICAL ou HIGH de autenticação ou privilégio ficou em aberto. No `task-manager-api`, `POST /users` com `"role": "admin"` grava `user`, e o token de login é um JWT HS256 com expiração. Evidência em [Logs das aplicações](#logs-das-aplicações-rodando-após-a-refatoração).

---

## A) Análise Manual

Os três projetos foram lidos arquivo por arquivo **antes** de a skill existir. A lista completa, com `arquivo:linha`, descrição e impacto de cada achado, está em **[`analise-manual.md`](analise-manual.md)**. Abaixo, o resumo e os achados de maior severidade.

Essa análise teve duas funções: definir o catálogo de anti-patterns da skill, e servir de **gabarito** para julgar se a skill funcionou. Sem ela, não haveria como distinguir um relatório bom de um relatório plausível.

| Projeto | Stack | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|---|---|---|---|
| `code-smells-project` | Python/Flask | 6 | 6 | 8 | 6 | **26** |
| `ecommerce-api-legacy` | Node/Express | 6 | 6 | 7 | 5 | **24** |
| `task-manager-api` | Python/Flask | 6 | 6 | 8 | 6 | **26** |

### Projeto 1 — `code-smells-project` (API de e-commerce)

| Severidade | Achado | Por que importa |
|---|---|---|
| CRITICAL | **SQL Injection generalizado** — 21 queries montadas por concatenação (`models.py:28,47-50,109-111,…`) | `POST /login` com `' OR '1'='1` autentica como o primeiro usuário da tabela. Ironicamente `database.py:70-83` usa placeholders corretamente nos seeds: o padrão certo existia e foi ignorado |
| CRITICAL | **Executor de SQL arbitrário** — `POST /admin/query` (`app.py:59-78`) | Acesso de DBA exposto à internet, sem autenticação |
| CRITICAL | **Reset de banco sem auth** — `POST /admin/reset-db` (`app.py:47-57`) | Perda total de dados por requisição anônima |
| CRITICAL | **Segredo hardcoded e vazado** — `app.py:7` e `controllers.py:288-289` | O `/health` público devolve a própria `SECRET_KEY`; com `debug=True` em `0.0.0.0`, o console do Werkzeug é execução remota de código |
| CRITICAL | **Senhas em claro, expostas pela API** — `models.py:84,100` | `GET /usuarios` anônimo devolve a senha de todos os usuários |
| CRITICAL | **God module** — `models.py:1-314`, `controllers.py:1-292` | Dados, negócio e formatação de 4 domínios em dois arquivos |
| HIGH | **Ausência de autenticação** — o `login` valida a senha e não emite credencial | Qualquer cliente altera preço, deleta produto e muda status de pedido alheio |
| HIGH | **Regra de negócio na camada de dados** — `models.py:133-169,235-273` | Faixas de desconto e checagem de estoque dentro de funções de repositório |
| HIGH | **Conexão global mutável** — `database.py:4-11`, `check_same_thread=False` | Cursores concorrentes sobre a mesma conexão; impossível injetar banco de teste |
| HIGH | **Escrita em 3 tabelas sem transação** — `models.py:133-169` | Falha no meio deixa pedido sem itens ou estoque debitado sem venda |
| HIGH | **Notificações no controller** — `controllers.py:208-210,247-250` | E-mail, SMS e push simulados com `print` dentro do handler HTTP |
| HIGH | **Roteamento manual sem Blueprints** — `app.py:11-30` | 15 rotas de 4 domínios registradas no entry point |

### Projeto 2 — `ecommerce-api-legacy` (LMS com checkout)

| Severidade | Achado | Por que importa |
|---|---|---|
| CRITICAL | **Cartão e chave de produção no log** — `src/AppManager.js:45` | O PAN completo e a `pk_live_` do gateway vão para stdout. Violação direta de PCI-DSS |
| CRITICAL | **Credenciais de produção versionadas** — `src/utils.js:2-4` | Segredo commitado é segredo vazado: rotacionar exige reescrever o histórico |
| CRITICAL | **Hash de senha caseiro** — `src/utils.js:17-23` | `badCrypto` concatena base64 do input 10.000 vezes e trunca em 10 caracteres. Custo alto, entropia quase nula — escrito para *parecer* key stretching |
| CRITICAL | **Pagamento aprovado pelo 1º dígito** — `src/AppManager.js:46` | `cc.startsWith("4")` substitui o gateway: receita fabricada e curso liberado de graça |
| CRITICAL | **Nenhuma rota autenticada** — `:28, :80, :131` | `/api/admin/financial-report` é público e devolve nome, e-mail e valor pago de todos os alunos |
| CRITICAL | **God class** — `src/AppManager.js:4-141` | Conexão, DDL, seed, rotas, checkout, pagamento e auditoria na mesma classe |
| HIGH | **Cadastro escondido no checkout** — `:66-72` | Senha omitida gera conta com a default `"123456"` |
| HIGH | **Checkout em 3 tabelas sem transação** — `:50-62` | Matrícula sem pagamento registrado |
| HIGH | **Contadores assíncronos manuais** — `:93-122` | Se um callback falha, o contador nunca zera e a requisição pendura até o timeout |
| HIGH | **Erros engolidos** — `:57, :104, :106, :133` | O `DELETE` responde 200 mesmo quando a query falha |
| HIGH | **Estado global exportado** — `src/utils.js:9-10,25` | `globalCache` cresce sem limite; `totalRevenue` é exportado por valor e nunca poderia funcionar |

### Projeto 3 — `task-manager-api` (gerenciador de tarefas)

Este projeto foi construído para parecer organizado. Tem `models/`, `routes/`, `services/`, `utils/`, Blueprints, ORM e hash de senha — **e a responsabilidade no lugar errado em todos eles**.

| Severidade | Achado | Por que importa |
|---|---|---|
| CRITICAL | **MD5 sem salt** — `models/user.py:29,32` | Quebrado desde 2004. E ter "criptografia" desarma a suspeita de quem lê rápido |
| CRITICAL | **Hash devolvido pela API** — `models/user.py:21` | `to_dict()` inclui `password`, e é o corpo de 4 endpoints públicos. Somado ao MD5, é a senha a um dicionário de distância |
| CRITICAL | **Credenciais SMTP hardcoded** — `services/notification_service.py:7-10` | Senha `'senha123'` no construtor |
| CRITICAL | **Segredo fixo e debug em `0.0.0.0`** — `app.py:13,34` | Console do Werkzeug acessível na rede |
| CRITICAL | **Autenticação de fachada** — `routes/user_routes.py:210` | `/login` devolve `'fake-jwt-token-' + id`: previsível, sem assinatura, e nenhuma rota o valida |
| CRITICAL | **Escalonamento de privilégio** — `routes/user_routes.py:42-78` | `POST /users` é público e aceita `role: 'admin'` do corpo |
| HIGH | **Regra de negócio reimplementada apesar de existir no model** | `Task.is_overdue()` está escrito e **nunca é chamado**; a mesma condição está copiada inline em 5 rotas |
| HIGH | **Validação duplicada com a camada morta** | `process_task_data()` existe para validar payload e nunca é chamada; os handlers revalidam à mão e **já divergiram** |
| HIGH | **Camada de serviço órfã** — `services/notification_service.py` | Nunca importado em lugar nenhum, e o `send_email` é SMTP síncrono dentro do ciclo de request |

---

## B) Construção da Skill

### Estrutura

```
.claude/skills/refactor-arch/
├── SKILL.md                          # orquestra as 3 fases e o gate — 165 linhas
└── references/
    ├── project-analysis.md           # heurísticas de detecção          (Fase 1)
    ├── antipattern-catalog.md        # 34 anti-patterns                 (Fase 2)
    ├── report-template.md            # formato do relatório             (Fase 2)
    ├── mvc-guidelines.md             # camadas alvo e regras L1–L7      (Fase 3)
    ├── refactoring-playbook.md       # 25 transformações antes/depois   (Fase 3)
    └── contract-baseline.md          # captura e diff do contrato       (Fase 3)
```

O `SKILL.md` é deliberadamente fino: descreve o fluxo, o gate e **quando carregar cada referência**. Cada fase lê apenas os arquivos de que precisa — a Fase 1 nunca carrega o playbook. É a mesma disciplina de separação que a skill impõe ao código auditado.

O `contract-baseline.md` é o sexto arquivo, além das cinco áreas exigidas, e existe por causa da decisão de validação descrita abaixo.

### Quatro decisões de design

**1. A Fase 2 pausa antes de tocar em qualquer arquivo.** O texto do gate é explícito sobre o que *não* conta como confirmação: *"'Parece bom', silêncio ou uma pergunta do usuário não são confirmação"*. Sem isso, um agente se autoriza sozinho. Nas três execuções o gate segurou — verificado por `git status` no momento da pausa: apenas o relatório apareceu, nenhum arquivo de projeto modificado.

**2. A refatoração preserva o contrato HTTP — exceto onde o contrato *é* a vulnerabilidade.** O enunciado pede duas coisas que colidem: *"eliminando os problemas encontrados"* e *"os endpoints originais continuam respondendo corretamente"*. A primeira versão resolveu a tensão adiando a autenticação, e o feedback mostrou que estava errada: deixar rota anônima para preservar o contrato é preservar o defeito. A regra atual é que **todo CRITICAL e HIGH é corrigido**, e o 401 do cliente anônimo é o conserto funcionando, não regressão. "Endpoints respondendo corretamente" passa a significar: o cliente com a credencial adequada recebe exatamente o que recebia antes.

**3. Quatro classes de exceção ao contrato, declaradas antes do gate.** Algumas correções mudam o contrato porque o elemento exposto *é* o achado: endpoint que só existe como vulnerabilidade, campo sensível no corpo da resposta, dado sensível em log, e rota que precisa de credencial. Cada exceção aplicada é listada nominalmente no relatório — no caso da autenticação, **uma linha por rota com o nível e o motivo** — antes do `[y/n]`. Consertos de bug que mudam status (ex.: 500 → 400 para corpo ausente) são declarados à parte, com os dois valores. O humano confirma sabendo exatamente o que muda.

**4. A validação é baseline + diff, não "subi e não deu erro".** Antes de modificar qualquer arquivo, a Fase 3 reseta o banco, sobe a aplicação original, dispara todos os endpoints e grava status, content-type e corpo. Depois de refatorar, repete e compara. Divergência não declarada é falha. Se a aplicação original não sobe, a Fase 3 **aborta** — sem baseline não há como provar nada.

### O catálogo: 34 anti-patterns (mínimo exigido: 8)

Derivados diretamente dos 76 findings da análise manual, distribuídos por severidade: 10 CRITICAL, 8 HIGH, 10 MEDIUM, 6 LOW. Inclui detecção de APIs deprecated (AP-19) com tabela de equivalentes modernos por stack.

Algumas entradas carregam **regras de anti-racionalização**, escritas porque um agente erra do mesmo jeito que um humano apressado:

- **AP-01 (injection):** *"Não rebaixe para MEDIUM só porque 'usar ORM facilitaria' — o achado é a injeção, não a ergonomia."*
- **AP-05 (hash):** *"Não avalie a qualidade do algoritmo. Implementação própria é o sinal, por si só."*
- **AP-09 (regra na camada errada):** *"A violação acontece nas duas direções. Aponte a camada exata."*

As duas primeiras existem porque a análise manual escorregou exatamente ali.

**Duas entradas foram inventadas**, por não existirem em catálogos padrão de code smells:

**AP-14 — Camada decorativa.** Código escrito na camada correta e nunca chamado, com a lógica duplicada na camada errada. Sinal de detecção: símbolo definido cuja contagem de referências no projeto é **1** — a própria definição. É o achado central do projeto 3, e é *pior* que ausência de camada: a estrutura desarma a suspeita enquanto as cópias divergem entre si. Disparou **só** no projeto 3, com 8 símbolos mais uma classe inteira.

**AP-33 — Integração crítica substituída por stub.** Decisão de negócio de alto impacto tomada por expressão local trivial, onde o domínio exige serviço externo. Esta entrada **não existia** na primeira versão: o projeto 2 aprova pagamento com `cc.startsWith("4")`, e a skill classificou como HIGH sob AP-09 (regra na camada errada). Não foi erro dela — era o enquadramento correto disponível. Faltava a entrada que distingue *onde* a regra mora de *se a regra é falsa*. A transformação correspondente (PB-23) é subtrativa: nomear o stub, isolá-lo atrás de uma interface e fazer barulho no boot — porque a refatoração não pode inventar a integração com um gateway que ninguém contratou.

**AP-34 — Privilégio atribuído por entrada do cliente.** Também ausente da primeira versão: no projeto 3, o cadastro público lia `role` do corpo e aceitava `admin`. A skill o enquadrava como validação ausente; o feedback mostrou que é escalonamento de privilégio, CRITICAL por si só. O PB-25 faz o papel virar default do servidor.

### O playbook: 25 transformações (mínimo exigido: 8)

Cada uma com exemplo antes/depois, referenciada por um ou mais anti-patterns. Cobrem parametrização de query, extração de config, quebra por domínio, hash com salt, N+1 → JOIN, transação com rollback, middleware de erro, Blueprints/Router, callback → async/await, API deprecated → equivalente moderno, serializer único, remoção de endpoint perigoso, determinismo de resposta, autenticação com token assinado e autorização por rota (PB-24), e papel definido pelo servidor (PB-25).

Verificação de integridade: **zero referência órfã** nos dois sentidos — todo `PB-NN` citado no catálogo existe no playbook, e todo `AP-NN` citado no playbook existe no catálogo. Todo anti-pattern tem transformação; a última lacuna, o AP-07, ganhou o PB-24 na reentrega.

### Agnosticismo de tecnologia — o mecanismo e a fronteira

**O mecanismo.** Cada anti-pattern é descrito por **sinal observável**, não por sintaxe, com uma tabela de manifestações por stack:

```markdown
### AP-04 — Segredo hardcoded
Sinal: literal com aparência de credencial atribuído a constante,
       campo de config ou argumento de conexão
Onde procurar: código-fonte · manifesto · lockfile
Manifestações:
  Python  app.config['SECRET_KEY'] = '...'  ·  smtplib.login('user','senha')
  Node    const config = { dbPass: '...', paymentGatewayKey: 'pk_live_...' }
  Geral   string com prefixo sk_ / pk_ / AKIA / ghp_ / xoxb-
Transformação: → PB-02
```

Adicionar uma stack é acrescentar uma linha na tabela; o sinal e a severidade não mudam. O campo `Onde procurar` existe porque o projeto 2 tem o código-fonte limpo de APIs deprecated e **nove pacotes podres no lockfile** — sem esse campo, a skill falharia um requisito obrigatório do enunciado.

**Evidência de que não é overfitting.** Um catálogo ajustado aos três projetos dispararia tudo em todos. Não foi o que aconteceu: o AP-14 disparou só no projeto 3; o AP-18 (resposta não-determinística) foi provado por execução só no projeto 2; e no projeto 2 o AP-08 (debug em bind público) não disparou pelo sinal de Flask — o console do Werkzeug, que não existe no Express —, e sim pelo equivalente da stack: o handler de erro padrão devolvendo stack trace com caminho absoluto, provado por execução. Isso é especificidade.

**A fronteira, declarada.** A skill é agnóstica **de framework, dentro de uma classe de sistema**: API HTTP sobre banco relacional. Não é agnóstica em sentido amplo, e os números do próprio repositório mostram isso — 44 blocos de exemplo em Python, 11 em JavaScript, 1 em SQL, **zero** em qualquer outra linguagem; Ruby, Java, PHP, Rust e C# não aparecem nas manifestações do catálogo. Mais importante: a estratégia de validação inteira depende de capturar respostas HTTP, então num CLI, numa biblioteca ou num job batch a Fase 3 abortaria.

Preferi declarar isso a alegar agnosticismo amplo. Alegação precisa resiste a quem abre o playbook; alegação ampla não.

### Desafios

**Os defeitos só apareceram executando.** A primeira versão passou nos critérios do projeto 1 e ainda assim tinha quatro defeitos, nenhum visível na leitura:

| Defeito | Como apareceu | Correção |
|---|---|---|
| Classificação de arquitetura por "pastas vs arquivos" | Projeto 1 classificado `Camadas decorativas` quando é `Monolítica` | Tabela trocada por **procedimento ordenado**, mais a regra "nome de arquivo não é fronteira" |
| AP-06 sem linha `Severidade:` | Herdava CRITICAL do cabeçalho da seção; o agente julgou HIGH pelo mérito, sem regra | Severidade condicional com teste objetivo |
| Metadado incoerente sem entrada | O `/health` se declara `"ambiente": "producao"` com `"debug": true` e nada pegava | Manifestação acrescentada ao AP-27 |
| Comentário contradizendo o código | `# Sem default: falta de segredo derruba o boot` acima de uma linha que gera chave aleatória | Comentário reescrito + `logger.warning` |

**A tensão entre fail-fast e "inicia sem erros".** O playbook prescrevia `os.environ["SECRET_KEY"]` para segredos. Está certo em produção e **errado nesta entrega**: quem clona o repositório e roda sem `.env` recebe `KeyError`, e o critério de aceite cai. O PB-02 passou a escolher entre falhar e avisar, proibindo apenas o silêncio. A implementação resultante emite `SECRET_KEY ausente: usando chave efêmera gerada no boot. Tokens emitidos não sobrevivem ao restart.`

**A prova de que a correção da classificação funcionou** veio nos dois projetos seguintes, em direções opostas e pelo mesmo procedimento: projeto 2 → `Monolítica`, projeto 3 → `Camadas decorativas`. A tabela antiga não conseguia acertar os dois. Na reexecução, o projeto 1 também saiu `Monolítica`.

**A recusa da primeira entrega: autenticação adiada.** A primeira versão tratava autenticação como decisão de produto para não quebrar o contrato, e os três relatórios terminavam com o AP-07 descrito e não aplicado. O avaliador recusou, com razão: um relatório que aponta um CRITICAL e o deixa de pé não entregou a refatoração. Mudar só a instrução ("aplique a autenticação") não bastava: o erro silencioso é proteger `PUT` e `DELETE` com dono-ou-admin e deixar `GET /users/<id>` com credencial simples, o que expõe o dado de qualquer usuário a quem se cadastrar. Daí a classificação obrigatória **uma linha por rota**, com a pergunta "de quem é esse dado?" respondida em cada uma, e o terceiro nível `dono ou admin` no middleware.

**Uma regra que o próprio agente descobriu.** O playbook dizia "escrita em dado sem dono (catálogo, categorias) → exige credencial". Na reexecução do projeto 1, a skill desviou dessa tabela por conta própria e exigiu admin em `POST/PUT/DELETE /produtos`, com o argumento de que, com cadastro público, "credencial" custa uma requisição — qualquer cliente recém-cadastrado poria o preço de um produto em 0,01. O projeto 3 seguiu a tabela e deixou as categorias com credencial simples. O argumento do projeto 1 virou regra do PB-24, e o projeto 3 foi reexecutado com ela.

**Relatório velho como risco de contaminação.** Os relatórios da primeira entrega, que adiavam a autenticação, continuavam em `reports/` — e um agente que os lesse poderia herdar escopo e decisões de uma execução descartada. A regra 9 do `SKILL.md` declara relatório anterior como histórico, não instrução, e o template manda sobrescrever. Para a reexecução do projeto 3, o projeto foi restaurado ao boilerplate (inclusive `__pycache__/` e `.venv/`, que mantinham pastas e pacotes da refatoração anterior visíveis à Fase 1).

---

## C) Resultados

### Findings por projeto

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total | Relatório |
|---|---|---|---|---|---|---|
| 1 — `code-smells-project` | 9 | 7 | 8 | 6 | **30** | [audit-project-1.md](reports/audit-project-1.md) |
| 2 — `ecommerce-api-legacy` | 8 | 7 | 6 | 6 | **27** | [audit-project-2.md](reports/audit-project-2.md) |
| 3 — `task-manager-api` | 8 | 4 | 8 | 6 | **26** | [audit-project-3.md](reports/audit-project-3.md) |

Em "Requires Product Decision", nenhum finding de autenticação ou privilégio. Ficaram só itens que dependem de informação de fora do código — ver [Pontos deixados em aberto](#pontos-deixados-em-aberto-deliberadamente).

### Fase 1 — saída real de cada execução

```
PHASE 1 · projeto 1
Stack:         Python 3.13.13 + Flask 3.1.1 (Werkzeug 3.1.9)
Dependencies:  flask-cors==5.0.1, sqlite3 (stdlib)
Domain:        E-commerce — catálogo de produtos, usuários/login, pedidos com baixa de estoque, relatório de vendas
Architecture:  Monolítica — 4 arquivos soltos na raiz sem fronteira de camada; models.py junta query + regra,
               controllers.py junta HTTP + validação + notificação + SQL, app.py junta rotas + SQL bruto
Files:         4 analyzed | ~780 lines of code
Routes:        19 endpoints
DB tables:     produtos, usuarios, pedidos, itens_pedido
```

```
PHASE 1 · projeto 2
Stack:         JavaScript (Node.js v22.18.0) + Express ^4.18.2 (instalado 4.22.1)
Dependencies:  express ^4.18.2, sqlite3 ^5.1.6 (instalado 5.1.7)
Domain:        LMS com checkout — alunos compram cursos (matrícula + pagamento) e admin consulta receita
Architecture:  Monolítica — God class AppManager.js abre conexão, monta SQL, decide regra e trata HTTP num só arquivo
Files:         3 analyzed | ~180 lines of code
Routes:        3 endpoints (POST /api/checkout, GET /api/admin/financial-report, DELETE /api/users/:id)
DB tables:     users, courses, enrollments, payments, audit_logs
```

```
PHASE 1 · projeto 3
Stack:         Python 3.13.13 + Flask 3.0.0 + Flask-SQLAlchemy 3.1.1 (SQLAlchemy 2.1.1)
Dependencies:  flask-cors 4.0.0, marshmallow 3.20.1 / requests 2.31.0 / python-dotenv 1.0.0 (declaradas, nunca importadas)
Domain:        Gerenciador de tarefas: usuários, categorias e tasks com status, prioridade, prazo e relatórios
Architecture:  Camadas decorativas — models/ e routes/ existem, mas Task.is_overdue/validate_status/validate_priority
               e utils.process_task_data nunca são chamados; a regra está duplicada inline nas rotas
Files:         15 analyzed | ~1158 lines of code
Routes:        22 endpoints
DB tables:     users, categories, tasks (SQLite → instance/tasks.db)
```

O campo `Architecture:` agora é persistido no relatório (cabeçalho de cada `audit-project-N.md`), e não só no stdout.

### Antes e depois da estrutura

Medido da árvore do git (`.py`/`.js`, excluindo `.claude/`):

| Projeto | Antes | Depois | Estrutura resultante |
|---|---|---|---|
| 1 | 4 arq / 780 linhas | 42 arq / 1164 linhas | `src/` com `config` · `database` · `models` · `services` · `controllers` · `views` · `middlewares` · `errors.py` + `app.py` como composition root |
| 2 | 3 arq / 180 linhas | 34 arq / 700 linhas | `src/` com `config` · `database` · `models` · `services` · `controllers` · `routes` · `middlewares` · `errors` + `create-app.js` (composition root) e `app.js` (só sobe o servidor) |
| 3 | 15 arq / 1158 linhas | 41 arq / 1381 linhas | `config` · `models` · `repositories` · `services` · `controllers` · `routes` · `middlewares` · `utils` · `exceptions.py` + `create_app()` |

O crescimento em linhas é fronteira de camada, autenticação (token, middleware, provisionamento de admin) e arquivos `__init__`, não lógica duplicada. No projeto 2, o número de linhas se manteve mesmo com autenticação nova: a troca de callbacks por driver síncrono eliminou a pirâmide de 7 níveis e os contadores manuais.

### Validação de contrato

A Fase 3 captura o baseline do código original **antes** de tocar em qualquer arquivo, refatora, captura de novo e compara. Com autenticação, a captura roda em três perfis: com a credencial adequada (tem de ser idêntico ao baseline), anônimo (tem de dar 401 nas rotas protegidas) e usuário comum (tem de dar 403 onde exige dono ou admin). Números recalculados por mim a partir das capturas em `.refactor-arch/`:

| Projeto | Autenticado: idênticas ao baseline | Divergências — todas declaradas antes do gate | Anônimo / sem permissão | Normalização declarada |
|---|---|---|---|---|
| 1 | 47 / 69 | 22: `senha` fora de `/usuarios` (3) · `secret_key`/`debug` do `/health` (2) · login com SQLi 200 → 401 (1) · `/admin/query` e `/admin/reset-db` → 404 (2) · consertos de bug 500 → 400 em corpo ausente ou tipo errado (10) · quantidade negativa, regra do `PUT` igual à do `POST`, e-mail duplicado, usuário inexistente (4) | 44 × 401 anônimo · 10 × 403 cliente em rota de admin ou de outro dono | `criado_em`, `token` |
| 2 | 14 / 15 | 1: JSON malformado — stack trace em HTML → `Bad Request` | smoke manual: 401 anônimo, 403 aluno no relatório e no `DELETE` de outro usuário, 200 admin | `capturedAt`, `token`; relatório ordenado por curso e aluno (a ordem do original era aleatória) |
| 3 | 68 / 79 | 11: `password` fora de quatro endpoints (8) · `role` do cadastro ignorado, inclusive valor inválido 400 → 201 (1) · 500 HTML → 500 JSON (2) | 66 × 401 anônimo · 18/18 sondas de autorização (dono, admin, token forjado, `fake-jwt-token`) | `created_at`, `updated_at`, `due_date`, `generated_at`, `timestamp`, `token` |

### Checklist de validação

Verificado de forma independente — capturas próprias, comparadores próprios, e aplicações subidas por mim.

| # | Item | P1 | P2 | P3 | Evidência |
|---|---|:--:|:--:|:--:|---|
| **Fase 1** | | | | | |
| 1 | Linguagem detectada corretamente | ✅ | ✅ | ✅ | Python 3.13 · Node 22.18 · Python 3.13 |
| 2 | Framework detectado corretamente | ✅ | ✅ | ✅ | versões instaladas conferidas: Flask 3.1.1 · Express 4.22.1 + sqlite3 5.1.7 · Flask 3.0.0 + SQLAlchemy 2.1.1 |
| 3 | Domínio descrito corretamente | ✅ | ✅ | ✅ | blocos da Fase 1 acima |
| 4 | Nº de arquivos condiz com a realidade | ✅ | ✅ | ✅ | 4/780 · 3/180 · 15/1158 — recontados por `git ls-tree` + `wc` |
| **Fase 2** | | | | | |
| 5 | Relatório segue o template | ✅ | ✅ | ✅ | os 3 relatórios em `reports/` |
| 6 | Cada finding tem arquivo e linhas exatos | ✅ | ✅ | ✅ | conferido por amostragem no código original dos 3 |
| 7 | Findings ordenados CRITICAL → LOW | ✅ | ✅ | ✅ | — |
| 8 | Mínimo de 5 findings | ✅ | ✅ | ✅ | 30 · 27 · 26 |
| 9 | Detecção de APIs deprecated incluída | ✅ | ✅ | ✅ | manifesto (P1) · lockfile (P2) · código-fonte (P3) — AP-19 nos 3 |
| 10 | Pausa e pede confirmação antes da Fase 3 | ✅ | ✅ | ✅ | `git status` no gate: só o relatório, zero arquivo de projeto |
| **Fase 3** | | | | | |
| 11 | Estrutura segue padrão MVC | ✅ | ✅ | ✅ | tabela de estrutura acima |
| 12 | Config em módulo próprio, sem hardcoded | ✅ | ✅ | ✅ | `SECRET_KEY`/`JWT_SECRET`, gateway, SMTP, debug e bind lidos do ambiente; `.env.example` sem valores |
| 13 | Models criados para abstrair dados | ✅ | ✅ | ✅ | `models/` (P1, P2) · `models/` + `repositories/` (P3) |
| 14 | Views/Routes separadas | ✅ | ✅ | ✅ | rotas só registram caminho, método e nível de acesso |
| 15 | Controllers concentram o fluxo | ✅ | ✅ | ✅ | zero SQL/query em controller |
| 16 | Error handling centralizado | ✅ | ✅ | ✅ | `middlewares/error_handler` nos 3, com exceções de domínio mapeadas para status |
| 17 | Entry point claro | ✅ | ✅ | ✅ | `app.py` / `create-app.js` + `app.js` / `create_app()` |
| 18 | Aplicação inicia sem erros | ✅ | ✅ | ✅ | subi as 3 pessoalmente — logs abaixo |
| 19 | Endpoints originais respondem | ✅ | ✅ | ✅ | 47/69 · 14/15 · 68/79 idênticos com credencial; o resto são as divergências declaradas |

### Logs das aplicações rodando após a refatoração

Cada aplicação subida do zero, com banco temporário e sem `.env` (por isso os avisos de chave efêmera no boot).

**Projeto 1** — boot, matriz de acesso e os exploits que funcionavam antes:

```
WARNING __main__: SECRET_KEY ausente: usando chave efêmera gerada no boot. Tokens emitidos não sobrevivem ao restart.
WARNING __main__: CORS_ORIGINS não definido: CORS liberado para todas as origens.
WARNING src.services.notificacao_service: Nenhum provedor de notificação configurado: e-mail, SMS e push rodam em modo stub (só log)
INFO src.database.seed: dados de exemplo inseridos

anon GET /                                   200
anon GET /produtos                           200
anon GET /usuarios                           401
anon GET /pedidos                            401
anon POST /produtos                          401
joao GET /usuarios (admin)                   403
joao GET /usuarios/1 (outro)                 403
joao GET /usuarios/2 (ele)                   200
joao PUT /produtos/1 (preço 0,01)            403
joao POST /pedidos em nome do usuário 3      403
joao POST /pedidos dele                      201
joao POST /pedidos quantidade -2             400      # antes: 201 com total negativo e estoque aumentado
admin GET /usuarios                          200      # sem o campo `senha`
admin GET /relatorios/vendas                 200
token forjado                                401
POST /admin/query                            404      # antes: executava SQL arbitrário
POST /login {"email": "admin@loja.com' --"}  401      # antes: 200 como Admin
GET /health → {"status":"ok","debug":false,...}       # sem `secret_key`
```

**Projeto 2** — com `ADMIN_EMAIL`/`ADMIN_PASSWORD` no ambiente:

```
{"level":"warn","message":"JWT_SECRET ausente: usando segredo efêmero gerado no boot. ..."}
{"level":"info","message":"conta admin provisionada","email":"admin@exemplo.com"}
{"level":"warn","message":"autorização de pagamento em modo STUB: cartões com prefixo \"4\" são aprovados sem cobrança","gatewayKeyConfigured":false}
{"level":"info","message":"processando pagamento","card":"****4444","amount":497}

anon GET /admin/financial-report                 401
anon DELETE /users/1                             401
login senha errada                               401
aluno GET /admin/financial-report                403
aluno DELETE /users/2 (outro)                    403
token forjado                                    401
admin GET /admin/financial-report                200
checkout público                                 200
checkout com card numérico                       400      # antes: derrubava o processo e o banco em memória
JSON malformado                                  400      # antes: stack trace com caminho absoluto
aluno DELETE /users/1 (ele mesmo)                200

PAN completo no log: 0 ocorrências
```

**Projeto 3** — depois de `python seed.py`:

```
anon GET /tasks, /tasks/<id>, /tasks/stats, /tasks/search, /users, /users/<id>,
     /users/<id>/tasks, /reports/summary, /reports/user/<id>     401 (todas)
anon GET /categories                           200
maria POST /categories                         403
maria PUT /categories/1                        403
maria DELETE /categories/1                     403
admin POST / PUT / DELETE /categories          201 / 200 / 200
maria PUT /tasks/1 (do João)                   403
maria PUT /tasks/2 (dela)                      200
maria POST /tasks                              201
maria GET /users/1                             403
maria GET /users/2                             200
maria GET /users                               403
admin GET /users                               200
token forjado                                  401
"Authorization: fake-jwt-token-1"              401
POST /users {"role": "admin"}                  201 → "role": "user", sem `password` no corpo
maria PUT /users/2 {"role": "admin"}           200 → "role": "user"
login → token "eyJhbGciOiJIUzI1NiIs..."        JWT HS256 com exp
DeprecationWarning / LegacyAPIWarning no log:  0
```

### Como a skill se comportou em stacks diferentes

**A adaptação ao ponto de partida funcionou.** O projeto 2 é um monolito de 3 arquivos e virou 34 módulos por domínio. O projeto 3 já tinha as pastas certas, e ali boa parte do trabalho foi **subtrativo**: passar a chamar `Task.is_overdue()`, `validate_status` e `validate_priority` e apagar as cópias inline, em vez de criar estrutura nova. Os dois caminhos vêm da mesma instrução, decidida pela classificação da Fase 1.

**A autenticação se adaptou à stack sem regra por linguagem.** Nos projetos Flask, a skill usou PyJWT; no Express, onde o projeto não tinha dependência de JWT, implementou HS256 sobre `node:crypto` para não adicionar pacote. Nos três, o middleware tem os mesmos três níveis e a rota declara o nível — só a sintaxe muda (decorator em Flask, array de middlewares em Express). O ponto de entrada também foi deduzido do código, e não de regra fixa: no projeto 2 o checkout é o único caminho que cria conta, e por isso ficou público; no projeto 1 e no 3, é o `POST` de cadastro.

**Conflito de porta, três estratégias.** As portas 5000 e 3000 estavam ocupadas na máquina de teste (AirPlay Receiver do macOS e apps locais). A skill resolveu sem editar o código original em nenhum dos casos: nos projetos Flask, `flask --app app run --port N` ignora o bloco `__main__`; no projeto Node, com a porta cravada num objeto de config, pré-carregar o módulo e mutar antes de carregar a app — o cache de `require` garante a mesma instância.

**Cada projeto exigiu uma normalização de diff diferente**, e nenhuma foi mais larga que o necessário. O projeto 2 mascarou só `capturedAt` e `token`, e ordenou um único endpoint, o que exigiu detectar a não-determinância por execução (o relatório financeiro do original devolvia os cursos em ordem diferente a cada chamada). O projeto 3 declarou os campos de timestamp. O projeto 1 usou `criado_em`, o nome em português da própria coluna — a skill adaptou ao projeto em vez de assumir nomes em inglês.

**A detecção de deprecated acertou um lugar diferente em cada projeto**, o que exercitou os três do campo `Onde procurar`: projeto 1 no **manifesto** (`flask-cors` com CVE), projeto 2 no **lockfile** (pacotes marcados como deprecated pelo npm), projeto 3 no **código-fonte** (`datetime.utcnow()` e `Query.get()` legado do SQLAlchemy).

**Ela achou coisas que a análise manual perdeu**, nos três projetos — entre elas o vazamento de stack trace do Express com o caminho absoluto do filesystem, o processo Node derrubado por um `card` numérico, a coluna `ativo` que existe no schema do projeto 1 e nunca é usada, e a quantidade negativa que *aumenta* o estoque no projeto 1. E corrigiu números meus: 22 endpoints no projeto 3, não 17; 15 arquivos e 1158 linhas, não 13 e ~900.

### Pontos deixados em aberto, deliberadamente

Nenhum é autenticação, autorização ou privilégio. Os relatórios marcam como `Requires Product Decision` só o que depende de informação de fora do código — a tabela "O que pode ficar sem correção" do `SKILL.md` define o critério.

| Projeto | Item | Por quê |
|---|---|---|
| 2 | **Gateway de pagamento real (AP-33, CRITICAL)** — cartão com prefixo `4` continua aprovado sem cobrança | A refatoração não pode inventar a integração com um gateway que ninguém contratou, e qual contratar não se deduz do código. O que era deduzível foi feito: a decisão saiu do handler para `StubPaymentGateway`, atrás de uma interface `authorize({ card, amount })` injetada no checkout; a classe se declara STUB no nome e no comentário; o boot emite `warn` informando que cartões com prefixo `4` são aprovados sem cobrança; o cartão sai mascarado no log e a chave do gateway saiu do código. Trocar essa classe é a única mudança que a integração real vai exigir |
| 1 | Provedor de notificação e devolução de estoque no cancelamento (AP-33, HIGH) | Mesmo caso: o stub foi isolado em `NotificacaoService`, com aviso no boot. Qual provedor de e-mail/SMS usar, e se o cancelamento repõe estoque (o original só imprimia "Devolver estoque"), são decisões de negócio |
| 1, 2 | Apagar registro com histórico (AP-24) | Apagar em cascata destrói registro de venda ou de pagamento; bloquear muda o contrato do `DELETE`; soft delete muda os relatórios. Comportamento atual preservado |
| 1, 3 | Origens do CORS (AP-26) | O mecanismo (`CORS_ORIGINS`) foi entregue; quais origens liberar só o dono do produto sabe. Default `*` com aviso no boot |
| 1, 2, 3 | Tamanho de página (AP-31) | `limit`/`offset` opcionais entregues nos projetos 1 e 3; forçar paginação muda o formato das listagens |
| 2 | Nomes públicos `usr`, `eml`, `pwd`, `c_id` (AP-29, parcial) | Renomear exige versionar a API; os nomes internos foram corrigidos |
| 1, 2, 3 | Token continua válido até expirar depois que o usuário é desativado, rebaixado ou apagado | O papel vai no token, para a autorização não depender de consulta ao banco. Revogação imediata exige lista de bloqueio ou checagem por requisição. A validade é de 12h e é configurável nos projetos Python |
| 3 | `user_id: 0` em `POST`/`PUT /tasks` | A checagem de existência usa teste de verdade e pula o `0`. Com `PRAGMA foreign_keys` ligado, o banco recusa a escrita: a resposta é 500 com rollback, sem dado corrompido |

---

## D) Como Executar

### Pré-requisitos

- **Claude Code** instalado e autenticado
- **Python 3.11+** e **Node.js 22.9+** (testado com Python 3.13 e Node 22.18; o `npm start` do projeto 2 usa `--env-file-if-exists`)
- Portas livres, ou a skill sobe em porta alternativa sozinha

### Preparar os ambientes

```bash
# projetos Python — um venv por projeto
cd code-smells-project && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

cd ../task-manager-api  && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python seed.py        # cria o schema e popula instance/tasks.db — rode antes do primeiro boot

# projeto Node
cd ../ecommerce-api-legacy && npm install
```

### Executar a skill

A skill é descoberta a partir do `.claude/skills/` do diretório onde a sessão começa, então **o cwd precisa ser a raiz do projeto**:

```bash
cd code-smells-project
claude
```

e, dentro da sessão, digite `/refactor-arch`.

> `claude "/refactor-arch"` como argumento único não dispara a skill — é tratado como mensagem. Entre com `claude` e digite o comando na sessão. Confirme com `/` no prompt: `refactor-arch` deve aparecer no autocomplete; se não aparecer, o cwd está errado.

Repita para os outros dois projetos, sempre com o cwd na raiz:

```bash
cd ../ecommerce-api-legacy && claude      # depois: /refactor-arch
cd ../task-manager-api     && claude      # depois: /refactor-arch
```

**Na Fase 2 a skill pausa.** Leia o relatório — em especial a tabela de rotas em `Contract Exceptions` e a seção `Requires Product Decision` — antes de responder `y`. Se aparecer autenticação ou privilégio em `Requires Product Decision`, algo saiu errado.

A skill grava o relatório em `reports/audit-<nome-do-projeto>.md`, na raiz do repositório. Os arquivos desta entrega foram renomeados para `audit-project-{1,2,3}.md`, como pede o enunciado.

### Validar que a refatoração funcionou

Sem token, as rotas protegidas respondem 401; com o token do papel certo, respondem como antes.

```bash
# Projeto 1
cd code-smells-project && PORT=5077 .venv/bin/python app.py &
B=localhost:5077; J='Content-Type: application/json'
curl -s -o /dev/null -w '%{http_code}\n' $B/usuarios                       # 401
TOKEN=$(curl -s -H "$J" -d '{"email":"admin@loja.com","senha":"admin123"}' $B/login \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["token"])')
for p in / /produtos /produtos/1 /produtos/9999 /usuarios /pedidos /relatorios/vendas /health; do
  printf '%-22s %s\n' "$p" "$(curl -s -o /dev/null -w '%{http_code}' -H "Authorization: Bearer $TOKEN" $B$p)"
done                                                                        # 200 em tudo, 404 em /produtos/9999

# Projeto 2 — o admin vem do ambiente
cd ../ecommerce-api-legacy && PORT=3077 ADMIN_EMAIL=admin@exemplo.com ADMIN_PASSWORD=troque-esta-senha npm start &
TOKEN=$(curl -s -H 'Content-Type: application/json' -d '{"eml":"admin@exemplo.com","pwd":"troque-esta-senha"}' \
  localhost:3077/api/login | python3 -c 'import sys,json; print(json.load(sys.stdin)["token"])')
curl -s -o /dev/null -w '%{http_code}\n' localhost:3077/api/admin/financial-report                                    # 401
curl -s -o /dev/null -w '%{http_code}\n' -H "Authorization: Bearer $TOKEN" localhost:3077/api/admin/financial-report  # 200

# Projeto 3 — rode o seed antes
cd ../task-manager-api && .venv/bin/python seed.py && PORT=5078 .venv/bin/python app.py &
TOKEN=$(curl -s -H 'Content-Type: application/json' -d '{"email":"joao@email.com","password":"1234"}' \
  localhost:5078/login | python3 -c 'import sys,json; print(json.load(sys.stdin)["token"])')
for p in /tasks /users /categories /reports/summary; do
  printf '%-18s %s\n' "$p" "$(curl -s -o /dev/null -w '%{http_code}' -H "Authorization: Bearer $TOKEN" localhost:5078$p)"
done                                                                        # 200 em tudo

# O diff de contrato: a Fase 3 imprime o resultado endpoint a endpoint e grava as capturas
# em .refactor-arch/, que é ignorado pelo git — o diretório só existe depois de rodar a skill.
# Divergências devem corresponder exatamente às exceções declaradas antes do gate.

# As regras de camada valem (exemplo no projeto 1)
grep -rE "import sqlite3|from database" src/views/      # esperado: vazio
grep -rE "SELECT |INSERT |\.execute\(" src/controllers/  # esperado: vazio
grep -rE "from flask|jsonify" src/models/                # esperado: vazio
```

### Resetar entre execuções

A Fase 3 modifica o projeto. Para reexecutar a partir do código original, preservando a skill:

```bash
P=task-manager-api                       # ou code-smells-project / ecommerce-api-legacy
mv $P/.refactor-arch /tmp/                # capturas da execução anterior
git restore --source=6d1ce62 --staged --worktree -- $P ":(exclude)$P/.claude"
find $P -name __pycache__ -not -path '*/.venv/*' -prune -exec rm -rf {} +
git clean -nd $P                          # confira a lista; depois git clean -fd $P
```

`6d1ce62` é o commit do boilerplate. O `:(exclude)` é necessário porque a skill é versionada e não existe nesse commit — sem ele, o `restore` a apagaria. O `__pycache__/` precisa sair antes do `git clean`, senão as pastas criadas pela refatoração sobrevivem e a Fase 1 enxerga camadas que o original não tem. Nos projetos Python, recrie também o `.venv` com o `requirements.txt` original, para a checagem de dependências ver as versões reais.

### Ordem sugerida

1. Preparar os três ambientes e confirmar que as aplicações sobem **antes** de qualquer refatoração — sem baseline, a Fase 3 aborta.
2. Executar no `code-smells-project` (monolito, o caso mais simples).
3. Executar no `ecommerce-api-legacy` (outra stack).
4. Executar no `task-manager-api` (o mais difícil: parece organizado e não está).
5. Se algum projeto não bater os critérios, ajustar os arquivos de referência — não o `SKILL.md`, salvo falha de orquestração —, redistribuir para as três cópias e reexecutar.
