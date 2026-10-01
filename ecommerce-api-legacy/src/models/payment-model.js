function createPaymentModel(db) {
    const insert = db.prepare('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)');

    return {
        create: ({ enrollmentId, amount, status }) => Number(insert.run(enrollmentId, amount, status).lastInsertRowid),
    };
}

module.exports = { createPaymentModel };
