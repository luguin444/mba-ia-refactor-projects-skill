const { PAYMENT_STATUS } = require('../models/constants');
const { hashPassword } = require('../services/password-service');

// Example data. The database is in memory by default, so the composition
// root runs this on boot unless SEED_ON_BOOT=false.
function seedExampleData(db) {
    db.transaction(() => {
        db.prepare('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)')
            .run('Leonan', 'leonan@fullcycle.com.br', hashPassword('123'));
        const insertCourse = db.prepare('INSERT INTO courses (title, price, active) VALUES (?, ?, 1)');
        insertCourse.run('Clean Architecture', 997.0);
        insertCourse.run('Docker', 497.0);
        db.prepare('INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)').run();
        db.prepare('INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, ?)').run(PAYMENT_STATUS.PAID);
    })();
}

module.exports = { seedExampleData };
