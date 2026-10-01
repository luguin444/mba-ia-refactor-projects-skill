function createAuditLogModel(db) {
    const insert = db.prepare("INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))");

    return {
        record: (action) => insert.run(action),
    };
}

module.exports = { createAuditLogModel };
