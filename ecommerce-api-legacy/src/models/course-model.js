// Acesso a dados de curso.

class CourseModel {
    constructor(db) {
        this.db = db;
    }

    findActiveById(id) {
        return this.db.get(
            'SELECT id, title, price, active FROM courses WHERE id = ? AND active = 1',
            [id],
        );
    }
}

module.exports = CourseModel;
