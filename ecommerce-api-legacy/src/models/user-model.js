function createUserModel(db) {
    const byEmail = db.prepare('SELECT id, name, email, pass, role FROM users WHERE email = ?');
    const insert = db.prepare('INSERT INTO users (name, email, pass, role) VALUES (?, ?, ?, ?)');
    const remove = db.prepare('DELETE FROM users WHERE id = ?');

    return {
        findByEmail: (email) => byEmail.get(email),
        create: ({ name, email, passwordHash, role }) => Number(insert.run(name, email, passwordHash, role).lastInsertRowid),
        deleteById: (id) => remove.run(id),
    };
}

module.exports = { createUserModel };
