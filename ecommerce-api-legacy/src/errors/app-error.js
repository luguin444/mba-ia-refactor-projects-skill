// Erro de negócio com status HTTP e mensagem que pode ser exposta ao cliente.
// Qualquer outro erro é tratado como interno pelo middleware e não vaza detalhe.

class AppError extends Error {
    constructor(message, status = 400) {
        super(message);
        this.name = 'AppError';
        this.status = status;
        this.expose = true;
    }
}

module.exports = AppError;
