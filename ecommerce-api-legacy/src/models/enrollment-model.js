function createEnrollmentModel(db) {
    const insert = db.prepare('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)');

    return {
        create: ({ userId, courseId }) => Number(insert.run(userId, courseId).lastInsertRowid),
    };
}

module.exports = { createEnrollmentModel };
