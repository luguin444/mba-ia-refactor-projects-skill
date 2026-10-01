const { AppError, failsWith } = require('../errors/app-error');
const { USER_ROLE } = require('../models/constants');
const { hashPassword } = require('./password-service');

class UserService {
    constructor({ users }) {
        this.users = users;
    }

    // A new account needs a string password, or none at all.
    assertCanCreateBuyer({ password }) {
        if (password && typeof password !== 'string') throw new AppError(400, 'Bad Request');
    }

    // Returns the id of the account with this email, creating it when absent.
    // A buyer created without a password gets no usable credential: login
    // refuses it, instead of accepting a well-known default password.
    findOrCreateBuyer({ name, email, password }) {
        const existing = failsWith('Erro DB', () => this.users.findByEmail(email));
        if (existing) return existing.id;

        this.assertCanCreateBuyer({ password });
        return failsWith('Erro ao criar usuário', () => this.users.create({
            name,
            email,
            passwordHash: password ? hashPassword(password) : null,
            role: USER_ROLE.STUDENT,
        }));
    }

    remove(id) {
        failsWith('Erro DB', () => this.users.deleteById(id));
    }
}

module.exports = { UserService };
