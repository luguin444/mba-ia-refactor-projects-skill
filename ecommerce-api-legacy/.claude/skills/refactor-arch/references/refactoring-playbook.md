# Playbook de refatoração

Usado na **Fase 3**. 22 transformações, referenciadas pelo catálogo.

Os exemplos usam Python e JavaScript porque são as stacks dos projetos de referência. A transformação é a mesma em qualquer linguagem — traduza o idioma, não a ideia.

**Ordem de aplicação:** config → dados → negócio → controllers → rotas → middleware de erro → entry point. Config primeiro porque todo o resto depende dela; entry point por último porque ele compõe o que já existe.

---

## PB-01 — Concatenação → query parametrizada
*Corrige AP-01*

```python
# antes
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
cursor.execute("SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'")

# depois
cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
```

Filtro dinâmico também é parametrizável — acumule placeholders e valores em paralelo:

```python
# antes
query = "SELECT * FROM produtos WHERE 1=1"
if termo:     query += " AND nome LIKE '%" + termo + "%'"
if categoria: query += " AND categoria = '" + categoria + "'"

# depois
query, params = "SELECT * FROM produtos WHERE 1=1", []
if termo:
    query += " AND nome LIKE ?"
    params.append(f"%{termo}%")
if categoria:
    query += " AND categoria = ?"
    params.append(categoria)
cursor.execute(query, params)
```

Nome de tabela e coluna não são parametrizáveis. Se precisarem ser dinâmicos, valide contra uma lista fechada.

---

## PB-02 — Literal → módulo de config
*Corrige AP-03, AP-08, AP-26*

```python
# antes — app.py
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
CORS(app)
app.run(host="0.0.0.0", port=5000, debug=True)
```

```python
# depois — src/config/settings.py
import os

class Settings:
    SECRET_KEY    = os.environ["SECRET_KEY"]
    DEBUG         = os.getenv("DEBUG", "false").lower() == "true"
    DATABASE_PATH = os.getenv("DATABASE_PATH", "loja.db")
    CORS_ORIGINS  = [o for o in os.getenv("CORS_ORIGINS", "").split(",") if o]
    HOST          = os.getenv("HOST", "127.0.0.1")
    PORT          = int(os.getenv("PORT", "5000"))

settings = Settings()
```

```python
# depois — entry point
app.config.from_object(settings)
CORS(app, origins=settings.CORS_ORIGINS)
app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
```

Regras: segredo sem default (`os.environ[...]` falha rápido se faltar); valor inofensivo pode ter default; `.env.example` versionado com as chaves e sem os valores; `.env` no `.gitignore`.

---

## PB-03 — God module → módulos por domínio
*Corrige AP-06, AP-13*

Separe **por domínio primeiro, por camada depois**.

```
# antes
models.py        (4 domínios, 314 linhas)
controllers.py   (4 domínios, 292 linhas)

# depois
src/models/produto_model.py       src/controllers/produto_controller.py
src/models/usuario_model.py       src/controllers/usuario_controller.py
src/models/pedido_model.py        src/controllers/pedido_controller.py
src/models/relatorio_model.py     src/controllers/relatorio_controller.py
```

Uma pasta `models/` com um arquivo de 314 linhas não é separação — é o mesmo God module com endereço novo.

---

## PB-04 — Regra de negócio → camada própria
*Corrige AP-09, AP-11, AP-12*

```python
# antes — dentro do model (camada de dados decidindo negócio)
def relatorio_vendas():
    ...
    desconto = 0
    if faturamento > 10000:  desconto = faturamento * 0.1
    elif faturamento > 5000: desconto = faturamento * 0.05
```

```python
# depois — src/services/desconto_service.py
FAIXAS = ((10000, 0.10), (5000, 0.05), (1000, 0.02))

def calcular_desconto(faturamento: float) -> float:
    for minimo, taxa in FAIXAS:
        if faturamento > minimo:
            return faturamento * taxa
    return 0.0
```

O model volta a só ler e gravar; o service passa a ser testável sem banco.

Vale nas duas direções: validação de payload que vazou para o controller também sai dele, para um validador reutilizável.

---

## PB-05 — Hash próprio ou obsoleto → derivação com salt
*Corrige AP-05*

```python
# antes
self.password = hashlib.md5(pwd.encode()).hexdigest()
def check_password(self, pwd):
    return self.password == hashlib.md5(pwd.encode()).hexdigest()
```

```python
# depois
from werkzeug.security import generate_password_hash, check_password_hash

def set_password(self, pwd):
    self.password = generate_password_hash(pwd)          # scrypt + salt
def check_password(self, pwd):
    return check_password_hash(self.password, pwd)
```

```js
// antes
function badCrypto(pwd) {
  let hash = "";
  for (let i = 0; i < 10000; i++) hash += Buffer.from(pwd).toString('base64').substring(0, 2);
  return hash.substring(0, 10);
}

// depois
const { scrypt, randomBytes, timingSafeEqual } = require('node:crypto');
```

**Migração de hashes existentes:** senhas já gravadas não são reversíveis. Marque o registro como legado e re-hasheie no próximo login bem-sucedido. Se o projeto for seed-only, basta re-semear.

---

## PB-06 — N+1 → JOIN ou eager loading
*Corrige AP-17*

```python
# antes — 1 + N + N*M queries
for row in pedidos:
    itens = cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = ?", (row["id"],))
    for item in itens:
        prod = cursor3.execute("SELECT nome FROM produtos WHERE id = ?", (item["produto_id"],))
```

```python
# depois — 1 query
cursor.execute("""
    SELECT p.id, p.status, p.total, i.quantidade, i.preco_unitario, pr.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido i ON i.pedido_id = p.id
    LEFT JOIN produtos pr    ON pr.id = i.produto_id
    ORDER BY p.id
""")
# agrupe as linhas por pedido em memória
```

Com ORM, use o relacionamento que já está declarado:

```python
# antes
for t in Task.query.all():
    user = User.query.get(t.user_id)      # 1 query por task

# depois
from sqlalchemy.orm import joinedload
tasks = db.session.execute(
    select(Task).options(joinedload(Task.user), joinedload(Task.category))
).unique().scalars().all()
```

---

## PB-07 — Escritas soltas → transação com rollback
*Corrige AP-10*

```python
# antes
cursor.execute("INSERT INTO pedidos ...")
for item in itens:
    cursor.execute("INSERT INTO itens_pedido ...")
    cursor.execute("UPDATE produtos SET estoque = estoque - ? ...")
db.commit()
```

```python
# depois
try:
    cursor.execute("BEGIN")
    cursor.execute("INSERT INTO pedidos ...")
    for item in itens:
        cursor.execute("INSERT INTO itens_pedido ...")
        cursor.execute("UPDATE produtos SET estoque = estoque - ? ...")
    db.commit()
except Exception:
    db.rollback()
    raise
```

Em JS com callbacks, o mesmo se obtém com `db.serialize` + `BEGIN`/`COMMIT`/`ROLLBACK` explícitos, ou migrando para a API de promessas (PB-10) e envolvendo em `try/catch`.

---

## PB-08 — `try/except` repetido → middleware de erro
*Corrige AP-15, AP-21*

```python
# antes — repetido em 17 handlers
def listar_produtos():
    try:
        return jsonify({"dados": models.get_todos_produtos()}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
```

```python
# depois — src/middlewares/error_handler.py
class AppError(Exception):
    def __init__(self, mensagem, status=400):
        self.mensagem, self.status = mensagem, status
        super().__init__(mensagem)

def register_error_handlers(app):
    @app.errorhandler(AppError)
    def _app_error(e):
        return jsonify({"erro": e.mensagem, "sucesso": False}), e.status

    @app.errorhandler(Exception)
    def _unexpected(e):
        app.logger.exception("erro não tratado")
        return jsonify({"erro": "Erro interno", "sucesso": False}), 500
```

```python
# depois — o handler encolhe
def listar_produtos():
    return jsonify({"dados": produto_service.listar()}), 200
```

```js
// depois — Express: middleware de erro é o último a ser registrado, com 4 argumentos
app.use((err, req, res, _next) => {
  console.error(err);
  res.status(err.status || 500).json({ error: err.expose ? err.message : 'Erro interno' });
});
```

**Preserve o contrato:** mantenha os mesmos status codes e o mesmo formato de corpo que o baseline capturou. A mudança é onde o erro é tratado, não o que o cliente recebe. Pare de devolver `str(e)`, que vaza schema — mas se o baseline capturou uma mensagem específica em caminho de erro testado, ela precisa continuar igual.

---

## PB-09 — Rotas manuais → agrupamento por domínio
*Corrige AP-06*

```python
# antes — app.py, 15 rotas de 4 domínios
app.add_url_rule("/produtos", "listar_produtos", controllers.listar_produtos, methods=["GET"])
app.add_url_rule("/produtos/<int:id>", "buscar_produto", controllers.buscar_produto, methods=["GET"])
...
```

```python
# depois — src/views/produto_routes.py
from flask import Blueprint
from controllers import produto_controller

produto_bp = Blueprint("produtos", __name__)
produto_bp.add_url_rule("/produtos", view_func=produto_controller.listar, methods=["GET"])
produto_bp.add_url_rule("/produtos/<int:id>", view_func=produto_controller.buscar, methods=["GET"])
```

```python
# depois — entry point
for bp in (produto_bp, usuario_bp, pedido_bp, relatorio_bp):
    app.register_blueprint(bp)
```

Em Express, o equivalente é `express.Router()` por domínio, montado com `app.use('/produtos', produtoRouter)`.

**Atenção ao contrato:** ao montar um router com prefixo, confira que o caminho final continua idêntico ao original.

---

## PB-10 — Callback aninhado → async/await
*Corrige AP-16*

```js
// antes — 5 níveis, contadores manuais
this.db.get("SELECT * FROM courses WHERE id = ?", [cid], (err, course) => {
  this.db.get("SELECT id FROM users WHERE email = ?", [e], (err, user) => {
    this.db.run("INSERT INTO enrollments ...", [userId, cid], function (err) {
      self.db.run("INSERT INTO payments ...", [...], function (err) { ... });
    });
  });
});
```

```js
// depois — promisificado e linear
const { promisify } = require('node:util');

class Db {
  constructor(db) {
    this.get = promisify(db.get.bind(db));
    this.all = promisify(db.all.bind(db));
    this.run = (sql, p) => new Promise((res, rej) =>
      db.run(sql, p, function (err) { err ? rej(err) : res({ lastID: this.lastID }); }));
  }
}

const course = await db.get("SELECT * FROM courses WHERE id = ?", [cid]);
const user   = await db.get("SELECT id FROM users WHERE email = ?", [email]);
const { lastID: enrollmentId } = await db.run("INSERT INTO enrollments ...", [userId, cid]);
```

Contadores como `let pending = items.length` com `pending--` desaparecem: `await Promise.all(items.map(...))`.

---

## PB-11 — API deprecated → equivalente moderno
*Corrige AP-19*

```python
# antes
created_at = db.Column(db.DateTime, default=datetime.utcnow)
if self.due_date < datetime.utcnow():

# depois
from datetime import datetime, timezone
def _now(): return datetime.now(timezone.utc)

created_at = db.Column(db.DateTime, default=_now)
if self.due_date < _now():
```

```python
# antes — API legada do SQLAlchemy 1.x
task = Task.query.get(task_id)
tasks = Task.query.filter_by(status='pending').all()

# depois — SQLAlchemy 2.x
from sqlalchemy import select
task  = db.session.get(Task, task_id)
tasks = db.session.execute(select(Task).where(Task.status == 'pending')).scalars().all()
```

**Cuidado com fuso.** Trocar `utcnow()` por `now(timezone.utc)` torna o datetime *aware*. Comparar aware com naive levanta `TypeError`. Converta as duas pontas — inclusive o que vem do banco e o que vem do cliente — ou o diff de contrato vai acusar 500 onde antes havia 200.

Dependência deprecated no lockfile: atualize para a versão corrente, ou troque o pacote quando não houver versão saudável (`sqlite3` → `node:sqlite` no Node 22+).

---

## PB-12 — Dict montado à mão → serializer único
*Corrige AP-20, AP-22*

```python
# antes — o mesmo recurso com 3 formatos, espalhado por 3 arquivos
task_data = {}
task_data['id'] = t.id
task_data['title'] = t.title
...
```

```python
# depois — src/models/task_model.py, fonte única
class Task(db.Model):
    ...
    def to_dict(self, *, include_overdue: bool = False) -> dict:
        data = {
            "id": self.id, "title": self.title, "status": self.status,
            "priority": self.priority, "tags": self.tags.split(",") if self.tags else [],
        }
        if include_overdue:
            data["overdue"] = self.is_overdue()
        return data
```

Validação duplicada entre criar e atualizar segue a mesma ideia: um validador com modo parcial, chamado pelos dois.

**Preserve o contrato:** o serializer precisa emitir exatamente as chaves que o baseline capturou, na mesma forma. Se duas rotas emitiam formatos diferentes do mesmo recurso, o serializer precisa suportar as duas variações até que a divergência seja decidida — unificar é mudança de contrato.

---

## PB-13 — Remoção de endpoint perigoso
*Corrige AP-02 — exceção de contrato declarada*

```python
# antes
@app.route("/admin/query", methods=["POST"])
def executar_query():
    cursor.execute(request.get_json().get("sql", ""))
```

```python
# depois
# rota removida
```

Não substitua por versão "protegida" — um executor de SQL arbitrário por HTTP não tem versão segura. Declare a remoção no relatório antes do gate e registre no diff como divergência esperada.

---

## PB-14 — Remoção de dado sensível de log e resposta
*Corrige AP-04 — exceção de contrato declarada*

```js
// antes
console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`);

// depois
logger.info('processando pagamento', { last4: cc.slice(-4) });
```

```python
# antes
def to_dict(self):
    return {"id": self.id, "email": self.email, "password": self.password, ...}

# depois
def to_dict(self):
    return {"id": self.id, "email": self.email, ...}
```

Remova **apenas o campo sensível**; o resto do objeto continua idêntico. Liste no relatório quais endpoints mudam de forma.

---

## PB-15 — Camada decorativa → chamar o que já existe
*Corrige AP-14*

A transformação aqui é **subtrativa**. Não crie estrutura nova.

```python
# antes — models/task.py define, e ninguém chama
def is_overdue(self):
    if self.due_date:
        if self.due_date < datetime.utcnow():
            if self.status != 'done' and self.status != 'cancelled':
                return True
    return False

# antes — a mesma condição copiada em 5 rotas
if t.due_date:
    if t.due_date < datetime.utcnow():
        if t.status != 'done' and t.status != 'cancelled':
            task_data['overdue'] = True
        else:
            task_data['overdue'] = False
    ...
```

```python
# depois — models/task.py, uma vez
ESTADOS_FINALIZADOS = frozenset({"done", "cancelled"})

def is_overdue(self) -> bool:
    return (self.due_date is not None
            and self.due_date < _now()
            and self.status not in ESTADOS_FINALIZADOS)

# depois — nas rotas
task_data["overdue"] = t.is_overdue()
```

Procedimento: (1) confirme que o método existente e as cópias têm o mesmo comportamento — **as cópias costumam ter divergido**; (2) se divergiram, o comportamento do baseline manda; (3) apague as cópias e chame o método; (4) se o método estava errado, corrija-o e informe a divergência.

Código morto sem equivalente duplicado é PB-21, não este.

---

## PB-16 — Resposta não-determinística → ordem estável
*Corrige AP-18*

```js
// antes — push na ordem em que os callbacks terminam
courses.forEach(c => {
  this.db.all("SELECT * FROM enrollments WHERE course_id = ?", [c.id], (err, enr) => {
    report.push(courseData);          // ordem varia entre chamadas
  });
});
```

```js
// depois — a ordem vem da query, não do escalonamento
const courses = await db.all("SELECT * FROM courses ORDER BY id");
const report  = await Promise.all(courses.map(c => buildCourseReport(c)));
```

`Promise.all` preserva a ordem do array de entrada, independentemente da ordem de conclusão. Toda listagem ganha `ORDER BY` por chave estável.

Quando a não-determinância existia no baseline, a captura precisa ordenar antes de comparar (ver `contract-baseline.md`) — e a correção é relatada como melhoria, não como regressão.

---

## PB-17 — Integridade no schema
*Corrige AP-23, AP-24*

```sql
-- antes
CREATE TABLE usuarios (id INTEGER PRIMARY KEY, nome TEXT, email TEXT, senha TEXT);
CREATE TABLE pedidos  (id INTEGER PRIMARY KEY, usuario_id INTEGER, total REAL);

-- depois
CREATE TABLE usuarios (
  id    INTEGER PRIMARY KEY AUTOINCREMENT,
  nome  TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  senha TEXT NOT NULL
);
CREATE TABLE pedidos (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
  total      REAL NOT NULL DEFAULT 0
);
```

```python
# antes — cascade à mão
tasks = Task.query.filter_by(user_id=user_id).all()
for t in tasks:
    db.session.delete(t)
db.session.delete(user)

# depois — declarativo no relacionamento
tasks = db.relationship("Task", back_populates="user", cascade="all, delete-orphan")
```

Em SQLite, `FOREIGN KEY` só é aplicada com `PRAGMA foreign_keys = ON` por conexão.

**Cuidado com o contrato:** adicionar `NOT NULL` ou `UNIQUE` pode fazer uma requisição que antes passava virar erro. Confira contra o baseline antes de aplicar.

---

## PB-18 — Bootstrap → inicialização explícita
*Corrige AP-25*

```python
# antes — get_db() conecta, cria schema e insere dados de exemplo
def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect(db_path)
        cursor.execute("CREATE TABLE IF NOT EXISTS produtos ...")
        cursor.execute("SELECT COUNT(*) FROM produtos")
        if cursor.fetchone()[0] == 0:
            cursor.executemany("INSERT INTO produtos ...", produtos)
    return db_connection
```

```python
# depois — três responsabilidades, três lugares
# src/config/database.py   → só conexão
# src/database/schema.py   → só DDL, chamado por comando explícito
# src/database/seed.py     → só dados de exemplo, chamado por comando explícito
```

Se o projeto depende do seed automático para funcionar, mantenha o comportamento **acionado explicitamente** no boot em modo desenvolvimento — o baseline foi capturado com os dados semeados, e perdê-los muda toda resposta.

---

## PB-19 — Literais e nomes → constantes nomeadas
*Corrige AP-27, AP-29, AP-32*

```python
# antes
if faturamento > 10000: desconto = faturamento * 0.1
if categoria not in ["informatica", "moveis", "vestuario", "geral"]:
if novo_status not in ["pendente", "aprovado", "enviado", "entregue"]:
```

```python
# depois — src/models/constants.py
from enum import StrEnum

class StatusPedido(StrEnum):
    PENDENTE = "pendente"
    APROVADO = "aprovado"
    ENVIADO  = "enviado"

FAIXAS_DESCONTO = ((10_000, 0.10), (5_000, 0.05), (1_000, 0.02))
```

Nomes: `u`/`e`/`p` → `usuario`/`email`/`senha`; `cursor2`/`cursor3` desaparecem junto com o N+1 (PB-06).

**Não renomeie campo de API.** `usr`, `eml`, `c_id` no corpo da requisição são contrato. Renomeie a variável interna e mantenha a chave externa, ou declare a mudança.

```python
# antes → depois
if cond: return True
else:    return False     # → return cond
type(tags) == list        # → isinstance(tags, list)
"n: " + str(x)            # → f"n: {x}"
```

---

## PB-20 — `print` → logger estruturado
*Corrige AP-28*

```python
# antes
print("Produto criado com ID: " + str(id))
print("ERRO: " + str(e))
```

```python
# depois — src/config/logging.py
import logging
logger = logging.getLogger(__name__)

logger.info("produto criado", extra={"produto_id": id})
logger.exception("falha ao criar produto")
```

Nível por natureza: `info` para evento de negócio, `warning` para degradação, `error`/`exception` para falha. Nunca registre segredo, senha, hash ou dado de cartão (PB-14).

---

## PB-21 — Código morto → remoção
*Corrige AP-30*

Confirme com contagem de referências antes de apagar: se o símbolo aparece uma única vez no projeto, é a definição.

Ordem: (1) imports não usados; (2) funções e constantes nunca referenciadas; (3) ramos inalcançáveis.

Se o código morto duplica lógica que existe em outro lugar, use PB-15 — a resposta é chamar o que existe, não apagar os dois.

---

## PB-22 — Listagem → paginação
*Corrige AP-31*

```python
# antes
cursor.execute("SELECT * FROM produtos")

# depois
LIMITE_PADRAO, LIMITE_MAXIMO = 50, 200
limite  = min(int(request.args.get("limit", LIMITE_PADRAO)), LIMITE_MAXIMO)
offset  = int(request.args.get("offset", 0))
cursor.execute("SELECT * FROM produtos ORDER BY id LIMIT ? OFFSET ?", (limite, offset))
```

**Paginação muda o contrato** quando o baseline capturou a lista inteira. Duas saídas: manter o comportamento atual como default e aceitar `limit`/`offset` opcionais — o que preserva o contrato — ou declarar a mudança antes do gate. Prefira a primeira.
