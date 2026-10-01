function createCourseModel(db) {
    const activeById = db.prepare('SELECT id, title, price, active FROM courses WHERE id = ? AND active = 1');

    return {
        findActiveById: (id) => activeById.get(id),
    };
}

module.exports = { createCourseModel };
