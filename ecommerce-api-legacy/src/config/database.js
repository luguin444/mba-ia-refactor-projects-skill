const Database = require('better-sqlite3');

function openDatabase(path) {
    const db = new Database(path);
    db.pragma('foreign_keys = ON');
    return db;
}

module.exports = { openDatabase };
