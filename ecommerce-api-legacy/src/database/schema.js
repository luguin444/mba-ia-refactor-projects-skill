// enrollments.user_id has no FOREIGN KEY on purpose: what happens to
// enrollments and payments when a user is deleted is a pending product
// decision (AP-24), and the FK would make DELETE /api/users/:id fail.
const DDL = `
    CREATE TABLE IF NOT EXISTS users (
        id    INTEGER PRIMARY KEY,
        name  TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        pass  TEXT,
        role  TEXT NOT NULL DEFAULT 'student'
    );
    CREATE TABLE IF NOT EXISTS courses (
        id     INTEGER PRIMARY KEY,
        title  TEXT NOT NULL,
        price  REAL NOT NULL,
        active INTEGER NOT NULL
    );
    CREATE TABLE IF NOT EXISTS enrollments (
        id        INTEGER PRIMARY KEY,
        user_id   INTEGER NOT NULL,
        course_id INTEGER NOT NULL REFERENCES courses(id)
    );
    CREATE TABLE IF NOT EXISTS payments (
        id            INTEGER PRIMARY KEY,
        enrollment_id INTEGER NOT NULL REFERENCES enrollments(id),
        amount        REAL NOT NULL,
        status        TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS audit_logs (
        id         INTEGER PRIMARY KEY,
        action     TEXT NOT NULL,
        created_at DATETIME NOT NULL
    );
`;

function createSchema(db) {
    db.exec(DDL);
}

module.exports = { createSchema };
