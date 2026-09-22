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
├── SKILL.md                          # orquestra as 3 fases e o gate — 148 linhas
└── references/
    ├── project-analysis.md           # heurísticas de detecção          (Fase 1)
    ├── antipattern-catalog.md        # 33 anti-patterns                 (Fase 2)
    ├── report-template.md            # formato do relatório             (Fase 2)
    ├── mvc-guidelines.md             # camadas alvo e regras L1–L7      (Fase 3)
    ├── refactoring-playbook.md       # 23 transformações antes/depois   (Fase 3)
    └── contract-baseline.md          # captura e diff do contrato       (Fase 3)
```

O `SKILL.md` é deliberadamente fino: descreve o fluxo, o gate e **quando carregar cada referência**. Cada fase lê apenas os arquivos de que precisa — a Fase 1 nunca carrega o playbook. É a mesma disciplina de separação que a skill impõe ao código auditado.

O `contract-baseline.md` é o sexto arquivo, além das cinco áreas exigidas, e existe por causa da decisão de validação descrita abaixo.

### Quatro decisões de design

**1. A Fase 2 pausa antes de tocar em qualquer arquivo.** O texto do gate é explícito sobre o que *não* conta como confirmação: *"'Parece bom', silêncio ou uma pergunta do usuário não são confirmação"*. Sem isso, um agente se autoriza sozinho. Nas três execuções o gate segurou — verificado por `git status` no momento da pausa: apenas o relatório apareceu, nenhum arquivo de projeto modificado.

**2. A refatoração preserva o contrato HTTP.** O enunciado pede duas coisas que colidem: *"eliminando os problemas encontrados"* e *"os endpoints originais continuam respondendo corretamente"*. Corrigir os CRITICAL de autenticação faria toda rota responder 401 e quebraria o critério obrigatório. A regra adotada: corrigir tudo que é invisível ao cliente HTTP, e marcar os findings de autenticação como `REQUER DECISÃO DE PRODUTO`, com a transformação descrita e não aplicada.

**3. Três classes de exceção ao contrato, declaradas antes do gate.** Algumas correções mudam o contrato porque o elemento exposto *é* o achado: endpoint que só existe como vulnerabilidade, campo sensível no corpo da resposta, dado sensível em log. Cada exceção aplicada é listada nominalmente no relatório, antes do `[y/n]` — o humano confirma sabendo exatamente o que muda.

**4. A validação é baseline + diff, não "subi e não deu erro".** Antes de modificar qualquer arquivo, a Fase 3 reseta o banco, sobe a aplicação original, dispara todos os endpoints e grava status, content-type e corpo. Depois de refatorar, repete e compara. Divergência não declarada é falha. Se a aplicação original não sobe, a Fase 3 **aborta** — sem baseline não há como provar nada.

### O catálogo: 33 anti-patterns (mínimo exigido: 8)

Derivados diretamente dos 76 findings da análise manual, distribuídos por severidade: 9 CRITICAL, 8 HIGH, 10 MEDIUM, 6 LOW. Inclui detecção de APIs deprecated (AP-19) com tabela de equivalentes modernos por stack.

Algumas entradas carregam **regras de anti-racionalização**, escritas porque um agente erra do mesmo jeito que um humano apressado:

- **AP-01 (injection):** *"Não rebaixe para MEDIUM só porque 'usar ORM facilitaria' — o achado é a injeção, não a ergonomia."*
- **AP-05 (hash):** *"Não avalie a qualidade do algoritmo. Implementação própria é o sinal, por si só."*
- **AP-09 (regra na camada errada):** *"A violação acontece nas duas direções. Aponte a camada exata."*

As duas primeiras existem porque a análise manual escorregou exatamente ali.

**Duas entradas foram inventadas**, por não existirem em catálogos padrão de code smells:

**AP-14 — Camada decorativa.** Código escrito na camada correta e nunca chamado, com a lógica duplicada na camada errada. Sinal de detecção: símbolo definido cuja contagem de referências no projeto é **1** — a própria definição. É o achado central do projeto 3, e é *pior* que ausência de camada: a estrutura desarma a suspeita enquanto as cópias divergem entre si. Disparou **só** no projeto 3, com 8 símbolos mais uma classe inteira.

**AP-33 — Integração crítica substituída por stub.** Decisão de negócio de alto impacto tomada por expressão local trivial, onde o domínio exige serviço externo. Esta entrada **não existia** na primeira versão: o projeto 2 aprova pagamento com `cc.startsWith("4")`, e a skill classificou como HIGH sob AP-09 (regra na camada errada). Não foi erro dela — era o enquadramento correto disponível. Faltava a entrada que distingue *onde* a regra mora de *se a regra é falsa*. A transformação correspondente (PB-23) é subtrativa: nomear o stub, isolá-lo e fazer barulho na ausência da credencial — porque uma refatoração que preserva contrato não pode inventar a integração.

### O playbook: 23 transformações (mínimo exigido: 8)

Cada uma com exemplo antes/depois, referenciada por um ou mais anti-patterns. Cobrem parametrização de query, extração de config, quebra por domínio, hash com salt, N+1 → JOIN, transação com rollback, middleware de erro, Blueprints/Router, callback → async/await, API deprecated → equivalente moderno, serializer único, remoção de endpoint perigoso, e determinismo de resposta.

Verificação de integridade: **zero referência órfã** nos dois sentidos — todo `PB-NN` citado no catálogo existe no playbook, e todo `AP-NN` citado no playbook existe no catálogo. A única entrada sem transformação é o AP-07 (autenticação), por design.

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

**Evidência de que não é overfitting.** Um catálogo ajustado aos três projetos dispararia tudo em todos. Não foi o que aconteceu: o AP-14 disparou só no projeto 3; o AP-18 (resposta não-determinística) foi provado por execução só no projeto 2; e no projeto 2 a skill **recusou explicitamente** o AP-08 com justificativa correta — *"o Express não expõe console interativo"*. Isso é especificidade.

**A fronteira, declarada.** A skill é agnóstica **de framework, dentro de uma classe de sistema**: API HTTP sobre banco relacional. Não é agnóstica em sentido amplo, e os números do próprio repositório mostram isso — 39 blocos de exemplo em Python, 9 em JavaScript, 1 em SQL, **zero** em qualquer outra linguagem; Ruby, Java, PHP, Rust e C# não aparecem nas manifestações do catálogo. Mais importante: a estratégia de validação inteira depende de capturar respostas HTTP, então num CLI, numa biblioteca ou num job batch a Fase 3 abortaria.

Preferi declarar isso a alegar agnosticismo amplo. Alegação precisa resiste a quem abre o playbook; alegação ampla não.

### Desafios

**Os defeitos só apareceram executando.** A primeira versão passou nos critérios do projeto 1 e ainda assim tinha quatro defeitos, nenhum visível na leitura:

| Defeito | Como apareceu | Correção |
|---|---|---|
| Classificação de arquitetura por "pastas vs arquivos" | Projeto 1 classificado `Camadas decorativas` quando é `Monolítica` | Tabela trocada por **procedimento ordenado**, mais a regra "nome de arquivo não é fronteira" |
| AP-06 sem linha `Severidade:` | Herdava CRITICAL do cabeçalho da seção; o agente julgou HIGH pelo mérito, sem regra | Severidade condicional com teste objetivo |
| Metadado incoerente sem entrada | O `/health` se declara `"ambiente": "producao"` com `"debug": true` e nada pegava | Manifestação acrescentada ao AP-27 |
| Comentário contradizendo o código | `# Sem default: falta de segredo derruba o boot` acima de uma linha que gera chave aleatória | Comentário reescrito + `logger.warning` |

**A tensão entre fail-fast e "inicia sem erros".** O playbook prescrevia `os.environ["SECRET_KEY"]` para segredos. Está certo em produção e **errado nesta entrega**: quem clona o repositório e roda sem `.env` recebe `KeyError`, e o critério de aceite cai. O PB-02 passou a escolher entre falhar e avisar, proibindo apenas o silêncio. A implementação resultante emite `SECRET_KEY ausente: usando chave efêmera gerada no boot. Sessões assinadas não sobrevivem ao restart.`

**A prova de que a correção da classificação funcionou** veio nos dois projetos seguintes, em direções opostas e pelo mesmo procedimento: projeto 2 → `Monolítica`, projeto 3 → `Camadas decorativas`. A tabela antiga não conseguia acertar os dois.

**Uma limitação conhecida e não corrigida.** O `report-template.md` não persiste o campo `Architecture:` da Fase 1 — ele existe apenas no stdout. É o julgamento que amarra a estratégia da Fase 3 inteira, e ficar fora do arquivo quase me levou a concluir que a Fase 1 do projeto 3 havia falhado, quando o dado apenas não estava salvo.

---

## C) Resultados

### Findings por projeto

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total | Relatório |
|---|---|---|---|---|---|---|
| 1 — `code-smells-project` | 7 | 7 | 10 | 6 | **30** | [audit-project-1.md](reports/audit-project-1.md) |
| 2 — `ecommerce-api-legacy` | 5 | 7 | 8 | 6 | **26** | [audit-project-2.md](reports/audit-project-2.md) |
| 3 — `task-manager-api` | 5 | 5 | 9 | 6 | **25** | [audit-project-3.md](reports/audit-project-3.md) |

### Fase 1 — saída real de cada execução

```
PHASE 1 · projeto 1
Language:      Python 3.13
Framework:     Flask 3.1.1 (flask-cors 5.0.1)
Domain:        E-commerce — catálogo de produtos, usuários, pedidos e relatório de vendas
Architecture:  Camadas decorativas — models.py/controllers.py/database.py existem, mas
               a regra de negócio mora nos controllers e há SQL cru fora da camada de dados
Source files:  4 files analyzed | 780 lines
Routes:        19 endpoints
DB tables:     produtos, usuarios, pedidos, itens_pedido
```

```
PHASE 1 · projeto 2
Language:      JavaScript (Node.js v22.18.0, CommonJS)
Framework:     Express ^4.18.2 (4.22.1 instalado)
Domain:        LMS (plataforma de cursos) com checkout: usuário se matricula em curso e paga
Architecture:  Monolítica — AppManager.js concentra conexão, query, regra de negócio e HTTP
               no mesmo arquivo; utils.js é grab-bag (config + cache global + cripto)
Source files:  3 files analyzed | ~180 lines (AppManager.js 141, utils.js 25, app.js 14)
Routes:        3 endpoints
DB tables:     users, courses, enrollments, payments, audit_logs
```

```
PHASE 1 · projeto 3
Language:      Python 3.13.13
Framework:     Flask 3.0.0 (flask-sqlalchemy 3.1.1, SQLAlchemy 2.0.54, flask-cors 4.0.0)
Domain:        Gerenciador de tarefas — usuários, categorias, tasks com prazo/prioridade
Architecture:  Camadas decorativas — models/, routes/, services/ e utils/ existem, mas regra
               de negócio e validação moram nas rotas; Task.is_overdue() e
               helpers.process_task_data() estão escritos na camada certa e nunca são chamados
Source files:  15 files analyzed | ~1158 lines
Routes:        22 endpoints
DB tables:     users, categories, tasks (SQLite — instance/tasks.db)
```

**Ressalva honesta sobre o projeto 1:** ele foi executado com a primeira versão das referências, e a linha `Architecture:` está **errada** — 4 arquivos soltos na raiz são `Monolítica`, não `Camadas decorativas`, e a regra de negócio pesada mora em `models.py`, não nos controllers. Esse erro é o que produziu a correção descrita na seção B. Os projetos 2 e 3 rodaram com a versão corrigida e classificaram certo. A classificação não é item do checklist de validação, mas registrar o erro é mais útil que esconder.

### Antes e depois da estrutura

Medido da árvore do git, excluindo `.claude/` e artefatos de validação:

| Projeto | Antes | Depois | Estrutura resultante |
|---|---|---|---|
| 1 | 4 arq / 780 linhas | 37 arq / 1121 linhas | `config` · `database` · `models` · `services` · `controllers` · `views` · `middlewares` + composition root |
| 2 | 3 arq / 180 linhas | 28 arq / 834 linhas | `config` · `database` · `models` · `services` · `controllers` · `routes` · `middlewares` · `errors` + `create-app.js` |
| 3 | 15 arq / 1158 linhas | 39 arq / 1488 linhas | `config` · `models` · `repositories` · `services` · `controllers` · `routes` · `middlewares` · `exceptions` + composition root |

O crescimento em linhas é fronteira de camada e docstring, não lógica nova. O projeto 1 removeu 770 linhas dos quatro arquivos originais.

### Validação de contrato

| Projeto | Requisições capturadas | Idênticas | Divergências | Normalização declarada |
|---|---|---|---|---|
| 1 | 55 | 45 | 10 — 9 exceções declaradas + 1 derivada delas | `volatileFields: ["capturedAt", "criado_em"]` |
| 2 | 12 | 12 | 0 | `sortArraysBy: {"/api/admin/financial-report": "course"}` |
| 3 | 84 | 78 | 6 — 5 exceções declaradas + 1 conserto de bug | `volatileFields: ["created_at","updated_at","generated_at","timestamp"]` |

**As divergências, item por item.** Projeto 1: remoção de `/admin/query` e `/admin/reset-db` (404), do campo `senha` em `GET /usuarios` e `GET /usuarios/<id>`, e de `secret_key`/`debug`/`db_path` no `/health`. A décima é derivada: sem `/admin/reset-db`, o `/health` final observa estado acumulado. Projeto 3: remoção do campo `password` de quatro endpoints, mais `PUT /tasks/<id>` com `{"title": null}` saindo de **500** (`TypeError` não tratado, corpo HTML) para **400** `{"error": "Título é obrigatório"}` — o mesmo que o `POST` irmão já respondia. Aceito: um crash não é contrato.

### Checklist de validação

Verificado de forma independente — capturas próprias, comparadores próprios, e aplicações subidas por mim.

| # | Item | P1 | P2 | P3 | Evidência |
|---|---|:--:|:--:|:--:|---|
| **Fase 1** | | | | | |
| 1 | Linguagem detectada corretamente | ✅ | ✅ | ✅ | Python 3.13 · Node 22.18 · Python 3.13 |
| 2 | Framework detectado corretamente | ✅ | ✅ | ✅ | versões instaladas conferidas: Flask 3.1.1 · Express 4.22.1 + sqlite3 5.1.7 · Flask 3.0.0 |
| 3 | Domínio descrito corretamente | ✅ | ✅ | ✅ | blocos da Fase 1 acima |
| 4 | Nº de arquivos condiz com a realidade | ✅ | ✅ | ✅ | 4/780 · 3/180 · 15/1158 — recontados por `find` + `wc` |
| **Fase 2** | | | | | |
| 5 | Relatório segue o template | ✅ | ✅ | ✅ | os 3 relatórios em `reports/` |
| 6 | Cada finding tem arquivo e linhas exatos | ✅ | ✅ | ✅ | conferido por amostragem nos 3 |
| 7 | Findings ordenados CRITICAL → LOW | ✅ | ✅ | ✅ | — |
| 8 | Mínimo de 5 findings | ✅ | ✅ | ✅ | 30 · 26 · 25 |
| 9 | Detecção de APIs deprecated incluída | ✅ | ✅ | ✅ | manifesto · lockfile · código-fonte (um por projeto) |
| 10 | Pausa e pede confirmação antes da Fase 3 | ✅ | ✅ | ✅ | `git status` no gate: só o relatório, zero arquivo de projeto |
| **Fase 3** | | | | | |
| 11 | Estrutura segue padrão MVC | ✅ | ✅ | ✅ | tabela de estrutura acima |
| 12 | Config em módulo próprio, sem hardcoded | ✅ | ✅ | ✅ | grep dos segredos originais: zero ocorrências fora de `config/` |
| 13 | Models criados para abstrair dados | ✅ | ✅ | ✅ | — |
| 14 | Views/Routes separadas | ✅ | ✅ | ✅ | grep: zero import de driver/ORM em rotas |
| 15 | Controllers concentram o fluxo | ✅ | ✅ | ✅ | grep: zero SQL/query em controllers |
| 16 | Error handling centralizado | ✅ | ✅ | ✅ | `middlewares/error_handler` nos 3; zero `try/except` em controller ou rota no P3 |
| 17 | Entry point claro | ✅ | ✅ | ✅ | grep: zero rota definida no entry point |
| 18 | Aplicação inicia sem erros | ✅ | ✅ | ✅ | subi as 3 pessoalmente |
| 19 | Endpoints originais respondem | ✅ | ✅ | ✅ | 45/55 · 12/12 · 78/84 idênticos, divergências só as declaradas |

### Logs das aplicações rodando após a refatoração

**Projeto 1** — o exploit que funcionava antes da refatoração:

```
$ curl -X POST :5077/login -d '{"email":"a'"'"' OR '"'"'1'"'"'='"'"'1","senha":"x'"'"' OR '"'"'1'"'"'='"'"'1"}'
{"erro":"Email ou senha inválidos","sucesso":false}          # antes: autenticava

$ curl :5077/usuarios | head -c 120
{"dados":[{"criado_em":"...","email":"admin@loja.com","id":1,"nome":"Admin","tipo":"admin"}   # sem `senha`

$ curl :5077/health
{"ambiente":"producao","counts":{...},"database":"connected","status":"ok","versao":"1.0.0"}  # sem `secret_key`

GET /  200   GET /produtos  200   GET /produtos/9999  404   GET /relatorios/vendas  200
POST /admin/query  404   POST /admin/reset-db  404
```

**Projeto 2** — o log de pagamento, com a chave de gateway presente no ambiente:

```
$ PAYMENT_GATEWAY_KEY=pk_live_teste123 node src/app.js
[2026-09-22T02:00:40.284Z] INFO processando pagamento { last4: '4444' }

PAN completo no log?  0 ocorrências
pk_live no log?       0 ocorrências

$ # 6 checkouts em paralelo
enrollment_ids: [2, 3, 4, 5, 6, 7]   duplicados: False   erros de transação: 0

$ curl -X POST :3065/api/checkout -d '{"usr": broken'
Erro interno                                              # antes: stack trace HTML com o path absoluto

$ # 10 chamadas ao relatório financeiro
corpos distintos: 1                                       # antes: 5 corpos diferentes em 6 chamadas
```

**Projeto 3** — endpoints sensíveis a data, que eram o risco da refatoração:

```
GET /  200        GET /health  200          GET /tasks  200        GET /tasks/1  200
GET /tasks/9999  404                        GET /tasks/stats  200  GET /tasks/search?q=bug  200
GET /users  200   GET /users/1  200         GET /users/9999  404   GET /users/1/tasks  200
GET /categories  200                        GET /reports/summary  200   GET /reports/user/1  200

GET /tasks          → overdue: True
GET /tasks/stats    → overdue: 2 · completion_rate: 10.0
GET /reports/summary → overdue count: 2 · days_overdue do 1º: 3
POST /tasks com due_date → 201
TypeError de timezone no log: 0 ocorrências

$ python seed.py
SECRET_KEY ausente: usando chave efêmera gerada no boot. Sessões assinadas não sobrevivem ao restart.
CORS_ORIGINS ausente: liberando todas as origens. Defina a lista de origens permitidas em produção.
```

Eliminação verificada por contagem no projeto 3: **18/18** `datetime.utcnow()` (a única sobrevivente está numa docstring), **51/51** `Model.query` legado, **12/12** `except:` nus.

### Como a skill se comportou em stacks diferentes

**A adaptação ao ponto de partida funcionou.** O projeto 2 é um monolito de 3 arquivos e virou 28 módulos por domínio. O projeto 3 já tinha as pastas certas, e ali o trabalho foi **subtrativo**: passar a chamar `Task.is_overdue()` e apagar as 5 cópias inline, em vez de criar estrutura nova. Os dois caminhos vêm da mesma instrução, decidida pela classificação da Fase 1.

**Conflito de porta, três estratégias.** As portas 5000 e 3000 estavam ocupadas na máquina de teste (AirPlay Receiver do macOS e apps locais). A skill resolveu sem editar o código original em nenhum dos casos: nos projetos Flask, `flask --app app run --port N` ignora o bloco `__main__`; no projeto Node, com a porta cravada num objeto de config, pré-carregar o módulo e mutar antes de carregar a app — o cache de `require` garante a mesma instância.

**Cada projeto exigiu uma normalização de diff diferente**, e nenhuma foi mais larga que o necessário. O projeto 2 declarou `volatileFields: []` — **nada** mascarado — e ordenação em um único endpoint, o que exigiu detectar a não-determinância por execução: *"seis chamadas idênticas produziram cinco corpos diferentes"*. O projeto 3 declarou quatro campos de timestamp; conferi que as 16 requisições absorvidas por essa normalização diferem **exclusivamente** nesses quatro campos. O projeto 1 usou `criado_em`, o nome em português da própria coluna — a skill adaptou ao projeto em vez de assumir nomes em inglês.

**A detecção de deprecated acertou um lugar diferente em cada projeto**, o que exercitou os três do campo `Onde procurar`: projeto 1 no **manifesto** (`flask-cors` uma major atrás), projeto 2 no **lockfile** (9 pacotes marcados como deprecated pelo npm), projeto 3 no **código-fonte** (`datetime.utcnow()` e a API legada do SQLAlchemy).

**Ela achou coisas que a análise manual perdeu**, nos três projetos — entre elas o vazamento de stack trace do Express com o caminho absoluto do filesystem, a coluna `ativo` que existe no schema do projeto 1 e nunca é usada, e a divergência concreta entre `POST /categories` (400) e `PUT /categories/<id>` (500) no projeto 3. E corrigiu números meus: 22 endpoints no projeto 3, não 17; 15 arquivos e 1158 linhas, não 13 e ~900.

### Pontos deixados em aberto, deliberadamente

| Projeto | Item | Por quê |
|---|---|---|
| 1, 2, 3 | Autenticação (AP-07) | Implementar faria as rotas responderem 401 e quebraria o contrato. Decisão de produto |
| 2 | `ON DELETE CASCADE` nas matrículas | Apagar registro de pagamento porque um usuário foi removido destrói dado contábil. Hoje R$ 1.994 ficam atribuídos a um usuário inexistente; o conserto correto é soft delete ou `RESTRICT`, não cascade |
| 2 | Gateway de pagamento real | O stub foi nomeado, isolado e passou a avisar na ausência da credencial. Implementar integração é escopo de produto |
| 3 | Caminho de migração de hash MD5 | Existe e está correto, mas é **inalcançável** neste repositório: o `seed.py` grava scrypt, então nenhum registro nasce com MD5. Mantém `hashlib.md5` vivo no código |

---

## D) Como Executar

### Pré-requisitos

- **Claude Code** instalado e autenticado
- **Python 3.11+** e **Node.js 20+** (testado com Python 3.13 e Node 22)
- Portas livres, ou a skill sobe em porta alternativa sozinha

### Preparar os ambientes

```bash
# projetos Python — um venv por projeto, as versões de Flask diferem
cd code-smells-project && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

cd ../task-manager-api  && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python seed.py        # popula instance/tasks.db — rode antes do primeiro boot

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

**Na Fase 2 a skill pausa.** Leia o relatório — em especial as seções `Contract Exceptions` e `Requires Product Decision` — antes de responder `y`. Se `Contract Exceptions` estiver vazia num projeto que tem segredo exposto, algo saiu errado.

### Validar que a refatoração funcionou

```bash
# 1. a aplicação sobe
cd code-smells-project && PORT=5077 .venv/bin/python app.py

# 2. os endpoints respondem
for p in / /produtos /produtos/1 /produtos/9999 /usuarios /pedidos /relatorios/vendas /health; do
  printf '%-24s %s\n' "$p" "$(curl -s -o /dev/null -w '%{http_code}' localhost:5077$p)"
done
# esperado: 200 em tudo, 404 em /produtos/9999

# 3. o diff de contrato fechou
# A Fase 3 imprime o resultado endpoint a endpoint e grava as capturas em
# .refactor-arch/, que é ignorado pelo git — o diretório só existe depois de
# rodar a skill, não vem no clone. Divergências devem corresponder exatamente
# às exceções declaradas antes do gate.

# 3. as regras de camada valem
grep -rE "import sqlite3|from database" src/views/     # esperado: vazio
grep -rE "SELECT |INSERT |\.execute\(" src/controllers/ # esperado: vazio
grep -rE "from flask|jsonify" src/models/               # esperado: vazio
```

### Resetar entre execuções

A Fase 3 modifica o projeto. Para reexecutar do estado original:

```bash
git restore --source=6d1ce62 -- <projeto>/
```

`6d1ce62` é o commit do boilerplate. Isso preserva `.venv/`, `node_modules/` e a skill, que são ignorados pelo git.

### Ordem sugerida

1. Preparar os três ambientes e confirmar que as aplicações sobem **antes** de qualquer refatoração — sem baseline, a Fase 3 aborta.
2. Executar no `code-smells-project` (monolito, o caso mais simples).
3. Executar no `ecommerce-api-legacy` (outra stack).
4. Executar no `task-manager-api` (o mais difícil: parece organizado e não está).
5. Se algum projeto não bater os critérios, ajustar os arquivos de referência — não o `SKILL.md`, salvo falha de orquestração —, redistribuir com `rsync` e reexecutar.

A cópia canônica da skill vive em `code-smells-project/`. Para manter as três sincronizadas:

```bash
rsync -a --delete code-smells-project/.claude/skills/refactor-arch ecommerce-api-legacy/.claude/skills/
rsync -a --delete code-smells-project/.claude/skills/refactor-arch task-manager-api/.claude/skills/
```
