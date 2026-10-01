const { AppError, failsWith } = require('../errors/app-error');
const { verifyPassword } = require('./password-service');

class AuthService {
    constructor({ users, tokens }) {
        this.users = users;
        this.tokens = tokens;
    }

    login({ email, password }) {
        const user = failsWith('Erro DB', () => this.users.findByEmail(email));
        if (!user || !verifyPassword(password, user.pass)) throw new AppError(401, 'Unauthorized');
        return this.tokens.sign({ sub: user.id, role: user.role });
    }
}

module.exports = { AuthService };
