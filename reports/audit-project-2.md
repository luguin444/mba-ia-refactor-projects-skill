================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js v22.18.0) + Express ^4.18.2 (4.22.1 instalado) + sqlite3 ^5.1.6
Files:   3 analyzed | ~180 lines of code
Date:    2026-09-21

## Summary
CRITICAL: 5 | HIGH: 7 | MEDIUM: 8 | LOW: 6

## Findings

### [CRITICAL] Dado sensível em log (AP-04)
**File:** `src/AppManager.js:45`
**Description:** Cada checkout imprime no stdout o número do cartão completo recebido no body junto com a chave do gateway de pagamento (`pk_live_...`).
**Impact:** Qualquer pessoa com acesso ao log da aplicação — agregador, container, CI — coleta PAN de cartão e a chave de produção do gateway sem tocar no banco.
**Recommendation:** Remover o log. (→ PB-14, exceção de contrato declarada)

### [CRITICAL] Segredo hardcoded (AP-03)
**File:** `src/utils.js:2-5`
**Description:** `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_1234567890abcdef"` e `smtpUser` são literais no objeto `config`, versionados no repositório.
**Impact:** Credencial de produção no histórico do git: qualquer clone do repositório, hoje ou em qualquer commit passado, entrega a chave de pagamento e a senha do banco.
**Recommendation:** Mover para variáveis de ambiente com módulo de config que lê `process.env` e falha no boot se faltar. (→ PB-02)

### [CRITICAL] Hash de senha caseiro (AP-05)
**File:** `src/utils.js:17-23`, `src/AppManager.js:18, 68`
**Description:** `badCrypto` concatena 10.000 vezes os 2 primeiros caracteres do base64 da senha e trunca em 10 — o resultado é o mesmo prefixo repetido, sem salt, e o seed em `AppManager.js:18` grava a senha `'123'` em claro.
**Impact:** O espaço de saída é minúsculo e determinístico; recuperar a senha original a partir do "hash" é trivial, e o usuário seed já está em texto puro no banco.
**Recommendation:** Substituir por `bcrypt`/`scrypt` com salt por usuário; o seed passa a gravar o hash. (→ PB-05)

### [CRITICAL] God class (AP-06)
**File:** `src/AppManager.js:1-141`
**Description:** Um único arquivo abre a conexão SQLite (`:7`), executa todo o SQL (`:12-21, 37, 40, 50, 54, 57, 69, 83, 92, 104, 106, 133`), decide regra de negócio (`:46, 108-109`) e registra as rotas HTTP (`:28, 80, 131`) de quatro domínios — usuário, curso, matrícula e pagamento.
**Impact:** Condição CRITICAL do AP-06: acesso a dados e roteamento HTTP no mesmo arquivo — colapso completo das camadas. Nenhuma regra é testável sem subir um servidor HTTP e um banco.
**Recommendation:** Separar em repositories, services, controllers e routes, com a conexão injetada. (→ PB-03)

### [CRITICAL] Autenticação ausente (AP-07)
**File:** `src/AppManager.js:28, 80, 131`
**Description:** Nenhuma das três rotas lê header de autorização. `GET /api/admin/financial-report` devolve nome de todos os alunos e o faturamento por curso, e `DELETE /api/users/:id` apaga qualquer usuário por id.
**Impact:** Um `curl` anônimo lê o faturamento inteiro da operação e apaga qualquer conta.
**Recommendation:** Middleware de autenticação + autorização de papel na rota `/admin`. **Não aplicado nesta refatoração** — ver seção *Requires Product Decision*.

### [HIGH] Regra de negócio na camada errada (AP-09)
**File:** `src/AppManager.js:46, 108-109`
**Description:** A decisão de aprovar o pagamento (`cc.startsWith("4") ? "PAID" : "DENIED"`) vive dentro do handler de `POST /api/checkout`, e a regra de que só pagamento `PAID` entra no faturamento vive dentro do handler do relatório.
**Impact:** Duas regras centrais do domínio só existem dentro de closures de rota — não podem ser testadas, reusadas nem alteradas sem mexer no roteamento.
**Recommendation:** Extrair para `PaymentService.authorize()` e `FinancialReportService`. (→ PB-04)

### [HIGH] Escrita multi-entidade sem transação (AP-10)
**File:** `src/AppManager.js:50, 54, 57, 69`
**Description:** O checkout insere usuário, matrícula, pagamento e log de auditoria em quatro `db.run` encadeados por callback, sem `BEGIN`/`COMMIT` e sem rollback em nenhum dos caminhos de erro.
**Impact:** Falha no insert de pagamento (`:55`) deixa a matrícula gravada sem pagamento — o aluno fica com acesso ao curso sem cobrança, e não há como distinguir isso de uma matrícula legítima.
**Recommendation:** Envolver a operação numa transação única com rollback no erro. (→ PB-07)

### [HIGH] Estado global mutável (AP-11)
**File:** `src/utils.js:9-10, 25`, `src/AppManager.js:2, 59`
**Description:** `globalCache` é um objeto de módulo alimentado a cada checkout por `logAndCache` (`:59`) e nunca limpo; `totalRevenue` é um número exportado — quem importa recebe uma cópia congelada em `0`.
**Impact:** O cache cresce sem limite enquanto o processo viver (vazamento de memória) e é compartilhado entre todas as requisições; qualquer tentativa futura de usar `totalRevenue` lerá `0` para sempre, sem erro visível.
**Recommendation:** Remover o cache global; se um cache for necessário, instanciá-lo com limite e injetá-lo. (→ PB-04)

### [HIGH] Acesso a dados sem camada própria (AP-13)
**File:** `src/AppManager.js:37, 40, 50, 54, 57, 69, 83, 92, 104, 106, 133`
**Description:** Onze chamadas a `this.db.get/all/run` com SQL literal escritas dentro dos handlers HTTP.
**Impact:** Trocar SQLite por outro banco, ou testar qualquer rota sem banco real, exige reescrever os três handlers.
**Recommendation:** Repositories por entidade (`UserRepository`, `CourseRepository`, `EnrollmentRepository`, `PaymentRepository`, `AuditLogRepository`). (→ PB-03)

### [HIGH] Controle de fluxo assíncrono manual (AP-16)
**File:** `src/AppManager.js:26, 86-98, 93-122`
**Description:** O relatório financeiro usa dois contadores decrementados à mão (`coursesPending`, `enrPending`) para decidir quando responder, com aninhamento de quatro níveis de callback; o checkout mantém `const self = this` (`:26`) convivendo com arrow functions.
**Impact:** Se qualquer callback falhar, o contador nunca chega a zero e a requisição fica pendurada até o timeout do cliente — sem resposta e sem log.
**Recommendation:** Converter o driver para promises e usar `async/await` com `Promise.all`. (→ PB-10)

### [HIGH] Erro engolido silenciosamente (AP-15)
**File:** `src/AppManager.js:57, 92, 104, 106, 133`
**Description:** Cinco callbacks recebem `err` e nunca o checam. No `DELETE /api/users/:id` (`:133`) o erro é ignorado e a rota responde sucesso de qualquer forma; em `:92` um `err` faria `enrollments.length` lançar sobre `undefined`.
**Impact:** Uma falha de delete devolve 200 "Usuário deletado" sem ter deletado nada; uma falha no relatório derruba o processo ou pendura a requisição.
**Recommendation:** Propagar todos os erros para um middleware central. (→ PB-08)

### [HIGH] Efeito colateral escondido no fluxo (AP-12)
**File:** `src/AppManager.js:66-72`
**Description:** `POST /api/checkout` cria silenciosamente uma conta de usuário quando o e-mail não existe, e usa a senha default `"123456"` quando o campo `pwd` vem vazio (`:68`) — o campo não é validado em `:35`.
**Impact:** Contas nascem com senha conhecida sem que o dono saiba que tem conta; quem souber o e-mail entra com `123456`.
**Recommendation:** Separar criação de conta do checkout, ou exigir senha explicitamente. (→ PB-04)

### [MEDIUM] Queries N+1 (AP-17)
**File:** `src/AppManager.js:83, 92, 104, 106`
**Description:** O relatório busca todos os cursos, depois uma query de matrículas por curso, depois duas queries (usuário e pagamento) por matrícula.
**Impact:** Com 50 cursos e 200 matrículas cada, são 1 + 50 + 20.000 queries numa requisição sem paginação.
**Recommendation:** Uma query com `JOIN` e agregação no banco. (→ PB-06)

### [MEDIUM] Resposta não-determinística (AP-18)
**File:** `src/AppManager.js:96, 112, 119`
**Description:** `report` e `students` são montados por `push` dentro de callbacks concorrentes, sem `ORDER BY` em nenhuma query. **Confirmado por execução:** seis chamadas idênticas a `GET /api/admin/financial-report` produziram cinco corpos diferentes (ordem de cursos e de alunos varia).
**Impact:** Quebra qualquer cliente que indexe o array por posição, e impede diff de contrato sem normalização.
**Recommendation:** `ORDER BY` explícito nas queries e montagem determinística do array. O baseline da Fase 3 será normalizado (ordenado) antes do diff, já que a ordem atual não é um contrato observável. (→ PB-16)

### [MEDIUM] Schema sem constraints de integridade (AP-23)
**File:** `src/AppManager.js:12-16`
**Description:** Nenhuma das cinco tabelas declara `NOT NULL`, `UNIQUE` ou `FOREIGN KEY`; `users.email` não tem `UNIQUE` apesar de o código usar verifica-e-insere (`:40` → `:69`).
**Impact:** Dois checkouts concorrentes com o mesmo e-mail criam dois usuários duplicados; matrículas e pagamentos podem apontar para ids inexistentes sem o banco reclamar.
**Recommendation:** Adicionar `NOT NULL`, `UNIQUE (email)` e `FOREIGN KEY ... ON DELETE CASCADE` no DDL. (→ PB-17)

### [MEDIUM] Limpeza em cascata ausente (AP-24)
**File:** `src/AppManager.js:133-135`
**Description:** `DELETE FROM users` remove só o usuário; matrículas e pagamentos continuam apontando para o id removido — o próprio texto da resposta admite isso.
**Impact:** O relatório financeiro passa a listar `student: 'Unknown'` com receita contabilizada, e o faturamento fica atribuído a um usuário inexistente.
**Recommendation:** `ON DELETE CASCADE` no schema (→ PB-17). **O corpo da resposta é preservado literalmente**, inclusive a frase sobre os registros sujos, para não quebrar o contrato.

### [MEDIUM] Tratamento de erro repetido sem handler central (AP-21)
**File:** `src/AppManager.js:38, 41, 51, 55, 70, 84`
**Description:** Seis blocos `res.status(...).send("<texto>")` repetidos, com corpo em texto puro enquanto o sucesso é JSON, e nenhum middleware de erro registrado. **Confirmado por execução:** um body JSON malformado devolve o stack trace do Express em HTML, com o caminho absoluto do projeto no sistema de arquivos.
**Impact:** O cliente recebe formatos incoerentes (texto no erro, JSON no sucesso) e, no caminho não tratado, a estrutura de diretórios do servidor.
**Recommendation:** Middleware de erro central que serializa todo erro em JSON e não vaza stack. (→ PB-08)
**Nota:** o AP-08 (modo debug em bind público) não se aplica a esta stack — o Express não expõe console interativo; o vazamento de stack está coberto aqui.

### [MEDIUM] Contrato de resposta sem serializer único (AP-22)
**File:** `src/AppManager.js:60, 90, 112-115, 135`
**Description:** Cada resposta é um literal montado no ponto de uso: o checkout devolve `{msg, enrollment_id}`, o relatório monta `{course, revenue, students}` campo a campo, e o delete devolve uma frase em texto puro.
**Impact:** Não existe fonte única de verdade para o formato de nenhuma entidade; qualquer mudança precisa ser caçada rota a rota.
**Recommendation:** Presenters por recurso, usados por todos os controllers. (→ PB-12)

### [MEDIUM] Bootstrap acoplado à inicialização (AP-25)
**File:** `src/AppManager.js:10-23`, `src/app.js:9`
**Description:** `initDb()` cria as cinco tabelas e insere dados de exemplo (usuário `Leonan`, dois cursos, matrícula e pagamento) a cada boot, chamado direto de `app.js:9`.
**Impact:** Dados fictícios entram em qualquer ambiente que subir o processo, e não há versionamento de schema — o DDL é o próprio boot.
**Recommendation:** Separar migração de seed, com o seed condicionado a ambiente. (→ PB-18)
**Nota:** o banco é `:memory:` e o seed é o único estado que o baseline da Fase 3 observa — a separação preserva o mesmo estado inicial.

### [MEDIUM] Dependência deprecated (AP-19)
**File:** `package.json:11`, `package-lock.json` (9 ocorrências de `"deprecated"`)
**Description:** `sqlite3@5.1.6` arrasta a cadeia do `node-gyp` antigo: `inflight` (vaza memória), `glob` e `tar` em versões com vulnerabilidades publicadas, `npmlog`, `gauge`, `are-we-there-yet`, `rimraf<4`, `@npmcli/move-file` e `npmlog` — todos marcados como deprecated pelo registry.
**Impact:** Nove pacotes sem manutenção na árvore de produção, dois deles com CVEs conhecidos, por causa de um driver que o Node 22 já substitui nativamente.
**Recommendation:** Migrar para `node:sqlite` (nativo no Node 22) ou `better-sqlite3`. (→ PB-11)
**Nota:** a troca de driver muda o modelo de I/O (síncrono) mas não o contrato HTTP. Se a migração se mostrar arriscada durante a Fase 3, a refatoração mantém `sqlite3` atrás da camada de repositório e o finding permanece — o relatório final dirá qual caminho foi tomado.

### [LOW] Nomes não descritivos (AP-29)
**File:** `src/AppManager.js:29-33, 89, 102, 132`; contrato público em `api.http:8-12`
**Description:** Variáveis de negócio nomeadas `u`, `e`, `p`, `cid`, `cc`, `c`, `enr`, e campos de API `usr`, `eml`, `pwd`, `c_id`.
**Impact:** `e` para e-mail colide com a convenção de `error`, que é usada como `err` a duas linhas de distância (`:38`) — leitura ambígua no ponto mais crítico do fluxo.
**Recommendation:** Renomear as variáveis internas. **Os campos do body (`usr`, `eml`, `pwd`, `c_id`, `card`) são contrato público e ficam como estão.** (→ PB-19)

### [LOW] Magic numbers e literais repetidos (AP-27)
**File:** `src/AppManager.js:46, 68`, `src/utils.js:6, 19, 21, 22`
**Description:** O prefixo `"4"` que decide aprovação do cartão, a senha default `"123456"`, o loop de `10000` iterações, os cortes `substring(0,2)` / `substring(0,10)` e a porta `3000` são literais soltos na lógica.
**Impact:** A regra de aprovação de pagamento é um caractere no meio de um ternário — ninguém encontra para alterar.
**Recommendation:** Constantes nomeadas na camada de domínio; porta via ambiente. (→ PB-19)

### [LOW] `console.log` como logging (AP-28)
**File:** `src/AppManager.js:45`, `src/utils.js:13`, `src/app.js:13`
**Description:** Toda a saída de diagnóstico é `console.log`, sem nível, sem timestamp e sem destino configurável; `logAndCache` é uma função de log própria que só imprime e guarda em objeto.
**Impact:** Não há como baixar a verbosidade em produção nem separar erro de informação — inclusive no log do cartão (AP-04).
**Recommendation:** Logger com níveis, injetado. (→ PB-20)

### [LOW] Código e imports mortos (AP-30)
**File:** `src/AppManager.js:2`, `src/utils.js:10, 25`
**Description:** `totalRevenue` é importado em `AppManager.js:2` e nunca usado; `globalCache` é exportado em `utils.js:25` e nunca importado por ninguém.
**Impact:** Sugere um cálculo de faturamento centralizado que não existe — a lógica real está inline em `AppManager.js:109`.
**Recommendation:** Remover ambos. (→ PB-21)

### [LOW] Ausência de paginação (AP-31)
**File:** `src/AppManager.js:83, 92`
**Description:** `SELECT * FROM courses` e `SELECT * FROM enrollments WHERE course_id = ?` carregam as tabelas inteiras sem `LIMIT` nem cursor.
**Impact:** O relatório financeiro cresce linearmente com o catálogo e com a base de alunos, sem teto.
**Recommendation:** Paginação por cursor na listagem. (→ PB-22)
**Nota:** adicionar paginação mudaria o corpo da resposta — a Fase 3 mantém o formato atual e deixa o finding registrado.

### [LOW] Verbosidade evitável (AP-32)
**File:** `src/AppManager.js:26, 29-33, 43, 52, 81, 86, 90, 93, 132`
**Description:** `let` usado para dez valores que nunca são reatribuídos, e `const self = this` (`:26`) para contornar um `this` que as arrow functions do próprio arquivo já preservam.
**Impact:** `self` e `this` apontam para o mesmo objeto e são usados alternadamente nos callbacks (`:50` vs `:54`) — dá a impressão falsa de que há dois contextos diferentes.
**Recommendation:** `const` por padrão; eliminar `self`. (→ PB-19)

## Contract Exceptions
- src/AppManager.js:45 — log com o número do cartão e a chave do gateway removido (AP-04)

Nenhuma outra. Não há endpoint que exista apenas como vulnerabilidade (`DELETE /api/users/:id` é uma operação de negócio legítima sem auth, não um executor arbitrário), e nenhum corpo de resposta carrega campo sensível.

## Requires Product Decision
- **AP-07 — Autenticação ausente** (`src/AppManager.js:28, 80, 131`). Transformação descrita e **não aplicada**: middleware que valida credencial em todas as rotas, mais checagem de papel de administrador em `GET /api/admin/financial-report`. Aplicá-la faria as três rotas responderem 401 para as requisições de `api.http`, quebrando o contrato HTTP que esta refatoração se compromete a preservar. A decisão de quando introduzir auth — e qual esquema — é de produto.
- **AP-31 — Ausência de paginação** (`src/AppManager.js:83, 92`). Paginar mudaria o corpo de `GET /api/admin/financial-report` de array puro para objeto envelopado. Fica registrado, não aplicado.

================================
Total: 26 findings
================================
