================================
ARCHITECTURE AUDIT REPORT
================================
Project:      ecommerce-api-legacy
Stack:        JavaScript (Node.js v22.18.0) + Express ^4.18.2 (instalado 4.22.1)
Dependencies: express ^4.18.2, sqlite3 ^5.1.6 (instalado 5.1.7)
Domain:       LMS com checkout — alunos compram cursos (matrícula + pagamento) e admin consulta receita
Architecture: Monolítica — God class AppManager.js abre conexão (L7), monta SQL (L12-21, L37+), decide regra (L46) e trata HTTP (L28-137) num só arquivo
Files:        3 analyzed | ~180 lines of code
Routes:       3 endpoints (POST /api/checkout, GET /api/admin/financial-report, DELETE /api/users/:id)
DB tables:    users, courses, enrollments, payments, audit_logs
Date:         2026-09-30

## Summary
CRITICAL: 8 | HIGH: 7 | MEDIUM: 6 | LOW: 6

## Findings

### [CRITICAL] Autenticação ausente (AP-07)
**File:** `src/AppManager.js:80, 131-137` · nenhuma rota lê header de autorização; não existe login
**Description:** Condição CRITICAL: `DELETE /api/users/:id` é escrita destrutiva anônima sobre qualquer usuário, e `GET /api/admin/financial-report` devolve a anônimos o nome de cada aluno e quanto pagou. Não há emissão nem verificação de credencial em nenhum ponto do projeto.
**Impact:** Qualquer cliente na rede apaga a conta de qualquer usuário (`curl -X DELETE /api/users/1` → 200) e lista a receita e os alunos de todos os cursos.
**Recommendation:** (→ PB-24) Coluna `role` em `users` (default `'student'`). Nova rota pública `POST /api/login` (corpo `{eml, pwd}`, mesmos nomes do checkout) que valida a senha e devolve `{token}`; credencial inválida → 401. Token JWT HS256 assinado com `node:crypto` (sem dependência nova), segredo de `JWT_SECRET`, expiração de 12h, payload `{sub, role}`; sem `JWT_SECRET` no ambiente, o processo gera um segredo aleatório efêmero e loga aviso. Conta admin provisionada no bootstrap a partir de `ADMIN_EMAIL`/`ADMIN_PASSWORD` (sem as duas, nenhum admin existe e o relatório responde 403 a todos — falha fechada); o usuário do seed (Leonan) permanece `student`, porque nada no código diz que ele é admin. Middleware em `middlewares/` com três níveis — `requerAutenticacao`, `requerAdmin`, `requerDonoOuAdmin('id')` — aplicado por rota. Escopo, uma rota por linha:
- `GET    /api/admin/financial-report` → **admin** — relatório agregado que nomeia cada aluno e o valor pago (anônimo 401, não-admin 403)
- `DELETE /api/users/:id` → **dono ou admin** — id de sujeito no caminho, escrita destrutiva (anônimo 401, outro usuário 403)
- `POST   /api/checkout` → **público** — único caminho de entrada: é o checkout que cria a conta do aluno; exigir token fecharia a porta de cadastro
- `POST   /api/login` (nova) → **público** — emite a credencial

Respostas 401/403 em texto puro (`Unauthorized` / `Forbidden`), no mesmo estilo dos erros existentes. `api.http` e `README.md` atualizados com login, header `Authorization` e as variáveis de ambiente. Exceção de contrato declarada abaixo.

### [CRITICAL] Controle assíncrono manual — exceção em callback derruba o processo (AP-16)
**File:** `src/AppManager.js:26, 28-78` (pirâmide de 7 níveis), `86, 93, 98, 117-121` (contadores manuais), `46, 68, 93` (pontos de crash)
**Description:** Severidade elevada de HIGH para CRITICAL pela escala ("falha de segurança explorável"): exceções lançadas dentro dos callbacks do `sqlite3` escapam do pipeline do Express e matam o processo. Confirmado por execução — `card` não-string (`4111`, `["4"]`) quebra em `cc.startsWith` (L46) e `pwd` não-string quebra em `Buffer.from` (L68 → `utils.js:20`); erro na query de matrículas (L92) faria `enrollments.length` (L93) lançar do mesmo jeito.
**Impact:** Uma única requisição anônima (`{"card": 4111, ...}`) derruba a API e, como o banco é `:memory:`, apaga todos os dados — matrículas, pagamentos e contas.
**Recommendation:** (→ PB-10) Driver síncrono (`better-sqlite3`, ver AP-19) elimina callbacks e contadores; os handlers passam a ser funções lineares cujo `throw` o Express 4 captura e entrega ao middleware de erro. Some `const self = this`. Validação de tipo na entrada do checkout (e do login): `usr`, `eml`, `card` e `pwd` (quando presente) precisam ser string, `c_id` precisa ser número ou string numérica; caso contrário → 400 `Bad Request`, o mesmo status e corpo da validação atual. Mudança de comportamento declarada em Contract Exceptions.

### [CRITICAL] Número de cartão e chave do gateway em log (AP-04)
**File:** `src/AppManager.js:45`
**Description:** `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)` grava o PAN completo e a chave `pk_live_` em stdout a cada checkout, inclusive nos recusados. Confirmado no log de boot.
**Impact:** Qualquer pessoa ou sistema com acesso aos logs (agregador, CI, suporte) obtém cartões completos e a credencial de produção do gateway — violação direta de PCI-DSS.
**Recommendation:** (→ PB-14) Log substituído por `logger.info` com o cartão mascarado (só os 4 últimos dígitos) e sem a chave. Exceção de contrato declarada (log).

### [CRITICAL] Segredos hardcoded (AP-03)
**File:** `src/utils.js:2-5`
**Description:** `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_1234567890abcdef"`, `dbUser` e `smtpUser` literais no código versionado.
**Impact:** Toda cópia do repositório carrega a chave de produção do gateway; a chave deve ser considerada vazada e rotacionada independentemente da refatoração.
**Recommendation:** (→ PB-02) `src/config/env.js` lendo `process.env`: `PAYMENT_GATEWAY_KEY`, `PORT` (default 3000), `JWT_SECRET`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `DB_PATH` (default `:memory:`). `dbUser`, `dbPass` e `smtpUser` são removidos, não migrados — nunca são lidos (AP-30). `.env.example` com chaves sem valores reais; o `npm start` carrega `.env` se existir (`--env-file-if-exists`).

### [CRITICAL] Hash de senha caseiro e senha em claro (AP-05)
**File:** `src/utils.js:17-23` · `src/AppManager.js:18, 68`
**Description:** `badCrypto` repete 10.000 vezes os 2 primeiros caracteres do base64 da senha e trunca em 10 — o "hash" depende só dos 2 primeiros bytes da senha. O seed grava `pass = '123'` em claro.
**Impact:** Todas as senhas que começam com os mesmos dois caracteres têm o mesmo hash; reverter é trivial e não há sal.
**Recommendation:** (→ PB-05) `services/password-service.js` com `crypto.scrypt` (sal aleatório de 16 bytes por senha, formato `salt:hash`) e verificação por `timingSafeEqual`. O seed passa a gravar o hash de `'123'`. `badCrypto` removido. Sem impacto em contrato: nenhuma resposta expõe senha.

### [CRITICAL] Autorização de pagamento resolvida por prefixo do cartão (AP-33)
**File:** `src/AppManager.js:45-46` · `src/utils.js:4`
**Description:** Condição CRITICAL (o stub decide dinheiro): `cc.startsWith("4") ? "PAID" : "DENIED"` é a única decisão de cobrança; `paymentGatewayKey` existe na config e só é lido para ir ao log.
**Impact:** Qualquer string começando com "4" matricula o aluno e registra receita `PAID` que nunca foi cobrada — produto liberado de graça e relatório financeiro fabricado, sem erro em lugar nenhum.
**Recommendation:** (→ PB-23) Isolar a decisão em `services/payment-gateway.js` com interface `authorize({ card, amount }) → 'PAID' | 'DENIED'`, injetada no serviço de checkout; a implementação atual é mantida **como stub nomeado e documentado** (mesma regra do prefixo, para preservar o contrato) e recebe a chave via config. **Permanece em Requires Product Decision**: a integração real depende de qual gateway contratar.

### [CRITICAL] God class (AP-06)
**File:** `src/AppManager.js:1-141`
**Description:** Condição CRITICAL (dados **e** roteamento no mesmo arquivo): `AppManager` abre a conexão (L7), cria schema e seed (L10-23), monta todo o SQL, decide pagamento e receita, e registra as três rotas (L25-138), atendendo cinco entidades.
**Impact:** Nenhuma regra é testável sem subir HTTP e banco juntos; qualquer mudança em uma rota arrisca as outras.
**Recommendation:** (→ PB-03) Decompor em `config/`, `database/` (conexão, schema, seed), `models/` (um repositório por tabela), `services/` (checkout, relatório, usuário, senha, token, gateway), `controllers/`, `routes/`, `middlewares/` (auth, erro) e um composition root (`create-app.js`) que injeta as dependências; `app.js` só sobe o servidor. `AppManager.js` e `utils.js` deixam de existir.

### [CRITICAL] Stack trace exposto em bind público (AP-08)
**File:** `src/app.js:6, 12` · ausência de middleware de erro
**Description:** O servidor escuta em todas as interfaces (`*:3000`, confirmado com `lsof`), `NODE_ENV` não é definido e não há error handler: o handler padrão do Express devolve o stack trace. Confirmado — JSON malformado em `POST /api/checkout` responde 400 com HTML contendo o stack e caminhos absolutos do servidor (`/Users/.../node_modules/body-parser/lib/types/json.js:92:19`).
**Impact:** Qualquer cliente obtém o layout de diretórios, versões de bibliotecas e a estrutura interna enviando um corpo inválido.
**Recommendation:** (→ PB-02, PB-08) Middleware de erro central que nunca devolve stack: erro de parse do corpo → 400 `Bad Request` (texto, o mesmo corpo da validação existente); erro inesperado → 500 `Erro interno`; o stack vai só para o logger. O 404 de rota inexistente continua sendo o padrão do Express (não contém stack, contrato preservado). Bind mantido. Exceção de contrato declarada.

### [HIGH] Regra de negócio no handler HTTP (AP-09)
**File:** `src/AppManager.js:35, 46-48, 66-72, 108-110`
**Description:** Camada errada = handler HTTP: o handler de checkout valida entrada, decide pagamento e decide criar conta; o handler do relatório decide que receita conta só pagamento `PAID` enquanto `paid` do aluno mostra o valor independente do status.
**Impact:** As regras de receita e de matrícula só podem ser exercitadas por HTTP e não podem ser reutilizadas.
**Recommendation:** (→ PB-04) `CheckoutService.checkout()` (resolver conta, autorizar pagamento, matricular) e `FinancialReportService.build()` (regra de receita `PAID`, `paid = amount` ou 0 — semântica atual preservada). Controllers só traduzem request/response.

### [HIGH] Escrita multi-entidade sem transação (AP-10)
**File:** `src/AppManager.js:50-57, 69`
**Description:** Criação de usuário, matrícula, pagamento e auditoria são quatro `INSERT` encadeados em callbacks, sem `BEGIN`/`ROLLBACK`. A conta do comprador é criada (L69) **antes** da decisão de pagamento (L46), então um checkout recusado deixa a conta criada.
**Impact:** Falha entre os inserts deixa matrícula sem pagamento (curso liberado sem registro de cobrança) ou pagamento sem auditoria.
**Recommendation:** (→ PB-07) Autorização do pagamento antes de qualquer escrita; depois uma única transação (`db.transaction` do better-sqlite3) envolvendo criação de usuário (se novo), matrícula, pagamento e auditoria; falha em qualquer passo → rollback e 500 com a mensagem do passo (`Erro ao criar usuário`, `Erro Matrícula`, `Erro Pagamento`; auditoria → `Erro DB`). Efeito colateral declarado: checkout recusado deixa de criar conta (não visível por HTTP — nenhuma rota lista usuários).

### [HIGH] Erros engolidos silenciosamente (AP-15)
**File:** `src/AppManager.js:57, 92, 104, 106, 133`
**Description:** Cinco callbacks recebem `err` e nunca o checam: a falha da auditoria (L57) responde 200 `Sucesso`; o `DELETE` (L133) responde 200 "Usuário deletado" mesmo se o banco falhou; L92/104/106 ignoram erro no relatório.
**Impact:** O cliente recebe sucesso em operações que falharam, e o operador não tem nenhum registro do erro.
**Recommendation:** (→ PB-08) Todo erro de banco propaga ao middleware central e é logado. Falha no `DELETE` → 500 `Erro DB` (caminho de falha, não ocorre no baseline). `DELETE` de id inexistente continua 200 com a mesma mensagem — mudar para 404 alteraria o contrato e não é uma das exceções permitidas.

### [HIGH] Checkout cria conta silenciosamente com senha padrão (AP-12)
**File:** `src/AppManager.js:66-72` (cria conta), `68` (`p || "123456"`), `73-74` (conta existente)
**Description:** O checkout cria usuário como efeito colateral e, sem `pwd`, grava a senha fixa `123456`; para e-mail existente, ignora `usr` e `pwd` e matricula aquela conta.
**Impact:** Com o login introduzido pelo AP-07, toda conta criada sem `pwd` seria acessível por qualquer um com a senha `123456`.
**Recommendation:** (→ PB-04) Criação de conta explícita em `UserService.findOrCreateBuyer()`, chamada pelo checkout. Sem `pwd`, a conta é criada **sem credencial utilizável** (`pass = NULL`; o login a recusa com 401) em vez da senha padrão. O caminho de e-mail existente é mantido (é como um aluno recorrente compra; quem paga é o comprador) e o checkout permanece público. Respostas do checkout inalteradas.

### [HIGH] Acesso a dados sem camada própria (AP-13)
**File:** `src/AppManager.js:37, 40, 50, 54, 57, 69, 83, 92, 104, 106, 133`
**Description:** Os handlers chamam `this.db.get/run/all` diretamente com SQL literal — 11 queries dentro de rotas.
**Impact:** Trocar o schema ou o driver exige editar handlers HTTP; não há como testar regra sem banco.
**Recommendation:** (→ PB-03) Repositórios em `models/` (`user-model`, `course-model`, `enrollment-model`, `payment-model`, `audit-log-model`, `financial-report-model`) recebendo a conexão por injeção.

### [HIGH] Estado global mutável (AP-11)
**File:** `src/utils.js:9-15, 25` · `src/AppManager.js:2, 59`
**Description:** `globalCache` é objeto de módulo que recebe uma chave por checkout e nunca é lido (3 ocorrências: definição, escrita, export); `totalRevenue` é exportado **por valor** (cópia congelada em 0) e importado em `AppManager.js:2` sem uso.
**Impact:** Cache cresce sem limite durante a vida do processo (vazamento de memória) e o contador exportado é bug latente — quem o ler verá sempre 0.
**Recommendation:** (→ PB-04) Remover `globalCache`, `logAndCache` e `totalRevenue`: o cache é write-only, então removê-lo não tem efeito observável. A conexão passa a ser criada no composition root e injetada.

### [HIGH] Dependências com CVE conhecido e pacotes deprecated (AP-19)
**File:** `package.json:9-10` · `package-lock.json:37, 164, 767, 831, 1078, 1482, 1573, 1722, 2117`
**Description:** Condição HIGH (dependência fixada com CVE). `npm audit`: 12 vulnerabilidades (1 critical, 7 high, 1 moderate, 3 low). Via `express` 4.22.1: `path-to-regexp` GHSA-37ch-88jc-xwx2 (ReDoS, high), `qs` GHSA-q8mj-m7cp-5q26 / GHSA-x5fp-wj9c-mxmx / GHSA-4mjr-xmp4-gh2g (moderate), `body-parser` GHSA-v422-hmwv-36x6 (low). Via `sqlite3` 5.1.7 (direta, high): `tar` GHSA-34x7-hfp2-rc4v, GHSA-8qq5-rm4j-mr97 e mais 10 (critical), `node-gyp`/`make-fetch-happen`/`cacache`, `ip-address`, `brace-expansion` (high), `@tootallnate/once` (low). Lockfile: 9 pacotes deprecated (`@npmcli/move-file`, `are-we-there-yet`, `gauge`, `glob`, `inflight`, `npmlog`, `prebuild-install`, `rimraf`, `tar`). `npm outdated`: express 5.2.1 e sqlite3 6.0.1 disponíveis. Boot com `--trace-deprecation`: nenhum aviso.
**Impact:** Não é CRITICAL porque os CVEs de `tar` atingem a instalação/build, não o runtime, e o vetor do `path-to-regexp` exige múltiplos parâmetros por rota (o projeto só tem `:id`); ainda assim a árvore instalada carrega path traversal e DoS conhecidos.
**Recommendation:** (→ PB-11) `express` → `^4.22.3` (permanece na major 4: a 5 muda sintaxe de rota e tratamento de erro sem trazer correção que a 4.22.3 não traga). `sqlite3` → `better-sqlite3 ^13.0.3` (linha "Node 22+" do catálogo; API síncrona que viabiliza PB-07 e PB-10). Verificado em diretório temporário: essa combinação instala com **0 vulnerabilidades e 0 avisos de deprecated**; `sqlite3@6.0.1` também zera o audit mas ainda puxa `prebuild-install` deprecated.

### [MEDIUM] Queries N+1 no relatório financeiro (AP-17)
**File:** `src/AppManager.js:83, 89-92, 102-106`
**Description:** Para cada curso uma query de matrículas, e para cada matrícula uma de usuário e uma de pagamento: `1 + C + 2E` queries.
**Impact:** Com 100 cursos e 10.000 matrículas, um único GET dispara 20.101 queries.
**Recommendation:** (→ PB-06) Uma query: `courses LEFT JOIN enrollments LEFT JOIN users LEFT JOIN payments` ordenada, agregada no service. Curso sem matrícula continua com `students: []` e `revenue: 0`; aluno sem usuário continua `"Unknown"`; inclui cursos inativos, como hoje.

### [MEDIUM] Resposta não-determinística (AP-18)
**File:** `src/AppManager.js:83, 89-121`
**Description:** A ordem de cursos e alunos depende da ordem de conclusão dos callbacks e a query de cursos não tem `ORDER BY`. Confirmado: 8 chamadas idênticas produziram 7 corpos distintos.
**Impact:** Cliente que indexa o array recebe cursos trocados, e nenhum diff de contrato é possível sem normalização.
**Recommendation:** (→ PB-16) `ORDER BY courses.id, enrollments.id`. A ordem fixa é uma das ordens que o legado já produz; conteúdo idêntico. O diff de verificação compara o relatório normalizado (cursos e alunos ordenados). Declarado em Contract Exceptions.

### [MEDIUM] Tratamento de erro repetido sem handler central (AP-21)
**File:** `src/AppManager.js:38, 41, 51, 55, 70, 84`
**Description:** Seis `if (err) return res.status(...).send("...")` replicados; erros em texto puro enquanto o sucesso é JSON; nenhum middleware de erro (o padrão do Express responde em HTML).
**Impact:** Cada novo caminho de erro precisa reinventar status e mensagem, e um esquecido cai no handler padrão que vaza stack (AP-08).
**Recommendation:** (→ PB-08) `errors/app-error.js` (`status`, `message`) lançado pelos services e middleware central que responde `res.status(status).send(message)` — mesmos status e mesmos textos de hoje (`Bad Request`, `Curso não encontrado`, `Pagamento recusado`, `Erro DB`, ...), preservando o contrato.

### [MEDIUM] Schema sem constraints de integridade (AP-23)
**File:** `src/AppManager.js:12-16`
**Description:** DDL com 0 `NOT NULL`, 0 `UNIQUE`, 0 `FOREIGN KEY`. O e-mail é consultado (L40) e depois inserido (L69) sem `UNIQUE` — race de conta duplicada.
**Impact:** Dois checkouts simultâneos do mesmo e-mail criam duas contas; matrícula pode apontar para curso inexistente.
**Recommendation:** (→ PB-17) `NOT NULL` em toda coluna que o código trata como obrigatória (users.name/email/role, courses.*, enrollments.*, payments.*, audit_logs.*), `UNIQUE(users.email)`, FKs `enrollments.course_id → courses` e `payments.enrollment_id → enrollments`, `PRAGMA foreign_keys = ON` na conexão. `users.pass` fica nullable (AP-12). **Sem FK em `enrollments.user_id`** enquanto AP-24 não for decidido: com ela, apagar um usuário com matrícula falharia, mudando o contrato do `DELETE`.

### [MEDIUM] Limpeza em cascata ausente (AP-24)
**File:** `src/AppManager.js:131-137`
**Description:** `DELETE FROM users` deixa matrículas e pagamentos órfãos — a própria mensagem de resposta admite. Confirmado: após `DELETE /api/users/1`, o relatório lista `{"student":"Unknown","paid":997}`.
**Impact:** O relatório financeiro passa a mostrar receita de alunos inexistentes.
**Recommendation:** (→ PB-17) **Requires Product Decision**: apagar em cascata elimina registro financeiro de pagamento recebido; bloquear muda o contrato do `DELETE`; soft-delete muda o relatório. O que se pode fazer a um usuário com pagamento registrado não é dedutível do código. Comportamento atual (inclusive a mensagem) preservado.

### [MEDIUM] Bootstrap acoplado à inicialização (AP-25)
**File:** `src/app.js:9` · `src/AppManager.js:10-23`
**Description:** DDL e dados de exemplo são executados pelo boot via `initDb()` da God class, sem separação entre schema e seed.
**Impact:** Dados fictícios entram em qualquer ambiente que suba a aplicação, e não há como subir sem seed.
**Recommendation:** (→ PB-18) `database/schema.js` e `database/seed.js` como funções explícitas, chamadas pelo composition root. Como o banco é `:memory:` e o README documenta seed no boot, o seed continua habilitado por padrão (`SEED_ON_BOOT`, default `true`); provisionamento do admin (AP-07) separado do seed de exemplo.

### [LOW] `console.log` como logging (AP-28)
**File:** `src/app.js:13` · `src/AppManager.js:45` · `src/utils.js:13`
**Description:** Diagnóstico e auditoria por `console.log`, sem nível nem destino configurável.
**Impact:** Impossível filtrar ou silenciar por nível; erros não são registrados em lugar nenhum (AP-15).
**Recommendation:** (→ PB-20) `config/logger.js` com níveis (`LOG_LEVEL`), sem dependência nova.

### [LOW] Magic numbers e literais repetidos (AP-27)
**File:** `src/AppManager.js:21, 46, 48, 68, 108` · `src/utils.js:6, 19-22`
**Description:** `"4"` como regra de aprovação, `"123456"`, `10000`/`2`/`10` do hash, porta `3000`, e `'PAID'`/`'DENIED'` repetidos em quatro pontos.
**Impact:** Mudar um status exige caçar literais em SQL e em código.
**Recommendation:** (→ PB-19) `models/constants.js` com `PAYMENT_STATUS`; prefixo de aprovação confinado ao stub do gateway; porta default em `config/env.js`; `"123456"` e os números do hash desaparecem com AP-12 e AP-05.

### [LOW] Nomes não descritivos (AP-29)
**File:** `src/AppManager.js:29-33, 43, 52` · contrato: campos `usr`, `eml`, `pwd`, `c_id`, `card`
**Description:** `u`, `e`, `p`, `cid`, `cc` para dados de negócio (`e` colide com a convenção de erro); campos públicos abreviados.
**Impact:** Leitura lenta e propensa a erro, e o contrato público herda as abreviações.
**Recommendation:** (→ PB-19) Nomes internos `name`, `email`, `password`, `courseId`, `card`, com o mapeamento dos campos do corpo feito só no controller. Renomear os **campos públicos** fica em Requires Product Decision (exige versionar a API e migrar clientes).

### [LOW] Código e imports mortos (AP-30)
**File:** `src/utils.js:2, 3, 5, 10, 25` · `src/AppManager.js:2`
**Description:** `dbUser`, `dbPass`, `smtpUser` têm 1 ocorrência cada (só a definição); `totalRevenue` é importado em `AppManager.js:2` e nunca usado; `globalCache` é exportado e nunca importado. Nenhuma lógica equivalente duplicada em outra camada (não é AP-14).
**Impact:** Configuração morta com aparência de credencial confunde quem procura o que é usado.
**Recommendation:** (→ PB-21) Remover.

### [LOW] Ausência de paginação no relatório (AP-31)
**File:** `src/AppManager.js:83, 92`
**Description:** O relatório carrega todos os cursos e todas as matrículas, sem limite.
**Impact:** O tamanho da resposta cresce linearmente com o histórico de vendas.
**Recommendation:** (→ PB-22) **Requires Product Decision**: o relatório é agregado e paginá-lo muda o contrato; o tamanho de página (ou se o relatório deve ser paginado) é decisão do dono do produto. A query única do AP-17 reduz o custo enquanto isso.

### [LOW] Verbosidade evitável (AP-32)
**File:** `src/AppManager.js:29-33, 46, 52, 68, 81, 90`
**Description:** `let` para valores nunca reatribuídos e `function(err)` misturado com arrow functions por causa de `this.lastID`.
**Impact:** Ruído que esconde quais valores realmente mudam.
**Recommendation:** (→ PB-19) `const`; com o driver síncrono, `lastInsertRowid` elimina a necessidade de `function`.

## Contract Exceptions
- `src/AppManager.js:45` — log com número de cartão completo e chave do gateway substituído por log com os 4 últimos dígitos e sem chave (AP-04)
- Rotas com autenticação (AP-07), anônimo 200 → 401; cliente com credencial adequada recebe exatamente o que recebia antes:
    `GET    /api/admin/financial-report` — admin: anônimo 401, autenticado não-admin 403 — relatório nomeia todos os alunos e valores pagos
    `DELETE /api/users/:id` — dono ou admin: anônimo 401, outro usuário 403 — id de sujeito no caminho, escrita destrutiva
  permanecem públicas, deliberadamente:
    `POST   /api/checkout` — único caminho de entrada; é o checkout que cria a conta
    `POST   /api/login` — rota **nova** (aditiva), emite a credencial
- Stack trace no corpo de erro (AP-08) — alcance: **todas as rotas**, porque `express.json()` é global e qualquer requisição com `Content-Type: application/json` e corpo malformado passa por ele. Hoje: 400 com página HTML contendo stack e caminhos absolutos. Depois: 400 `Bad Request` (texto). Erros inesperados: hoje 500 HTML com stack; depois 500 `Erro interno`.
- Correção de bug que o baseline não consegue capturar (AP-16), alcance `POST /api/checkout` (e o novo `POST /api/login`), declarada com os dois valores:
    `card` não-string (número, array, objeto) — hoje: processo morre, sem resposta, banco em memória perdido — depois: 400 `Bad Request`
    `pwd` não-string para conta nova — hoje: processo morre — depois: 400 `Bad Request`
    `usr` ou `eml` não-string — hoje: 200 `Sucesso` com lixo persistido — depois: 400 `Bad Request`
    `c_id` que não é número nem string numérica — hoje: 404 (objeto) ou 200 (`true` vira curso 1) — depois: 400 `Bad Request`
- Ordem do `GET /api/admin/financial-report` (AP-18) — hoje: aleatória entre chamadas; depois: cursos por id, alunos por ordem de matrícula. Conteúdo idêntico; o diff compara o corpo normalizado.
- Sem efeito HTTP, declarados por transparência: checkout recusado deixa de criar a conta (AP-10); conta criada sem `pwd` deixa de receber a senha `123456` e fica sem credencial utilizável (AP-12); `globalCache` removido (AP-11).

## Requires Product Decision
- **AP-33** — integração real de pagamento: qual gateway contratar. A Fase 3 isola o stub atrás de uma interface, mas mantém a regra do prefixo "4" para preservar o contrato.
- **AP-24** — o que acontece com matrículas e pagamentos quando um usuário é apagado (cascata, bloqueio ou soft-delete). Comportamento atual preservado; FK em `enrollments.user_id` adiada até a decisão.
- **AP-31** — se o relatório financeiro deve ser paginado e com qual tamanho de página.
- **AP-29 (parcial)** — renomear os campos públicos `usr`, `eml`, `pwd`, `c_id` exige versionar a API; os nomes internos são corrigidos.

================================
Total: 27 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
