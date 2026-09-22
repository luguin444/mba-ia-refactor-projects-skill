// DDL explícito, acionado por chamada — não mais efeito colateral do boot (AP-25).

// Sobre as FOREIGN KEY abaixo: em SQLite elas só são aplicadas com
// `PRAGMA foreign_keys = ON`, que este projeto NÃO liga. O motivo é de contrato,
// não de descuido: ligar a checagem faria `DELETE /api/users/:id` ou falhar por
// restrição, ou apagar em cascata as matrículas e pagamentos — e o relatório
// financeiro logo depois do delete devolveria números diferentes dos que o
// baseline capturou. A decisão é do humano; ver AP-24 no relatório de auditoria.
const DDL = `
CREATE TABLE users (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name  TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    pass  TEXT NOT NULL
);

CREATE TABLE courses (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    title  TEXT NOT NULL,
    price  REAL NOT NULL,
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE enrollments (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id   INTEGER NOT NULL REFERENCES users(id),
    course_id INTEGER NOT NULL REFERENCES courses(id)
);

CREATE TABLE payments (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    enrollment_id INTEGER NOT NULL REFERENCES enrollments(id),
    amount        REAL NOT NULL,
    status        TEXT NOT NULL
);

CREATE TABLE audit_logs (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    action     TEXT NOT NULL,
    created_at DATETIME NOT NULL
);
`;

async function createSchema(db) {
    await db.exec(DDL);
}

module.exports = { createSchema };
