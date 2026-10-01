const { USER_ROLE } = require('../models/constants');
const { hashPassword } = require('../services/password-service');

// The admin account comes from the environment, never from the example seed.
// Without ADMIN_EMAIL and ADMIN_PASSWORD no admin exists and admin routes
// answer 403 to everyone.
function provisionAdmin(db, { adminEmail, adminPassword }, logger) {
    if (!adminEmail || !adminPassword) {
        logger.warn('ADMIN_EMAIL/ADMIN_PASSWORD ausentes: nenhuma conta admin provisionada; rotas administrativas responderão 403.');
        return;
    }
    db.prepare(`
        INSERT INTO users (name, email, pass, role) VALUES ('Admin', ?, ?, ?)
        ON CONFLICT(email) DO UPDATE SET pass = excluded.pass, role = excluded.role
    `).run(adminEmail, hashPassword(adminPassword), USER_ROLE.ADMIN);
    logger.info('conta admin provisionada', { email: adminEmail });
}

module.exports = { provisionAdmin };
