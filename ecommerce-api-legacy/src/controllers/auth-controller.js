const { AppError } = require('../errors/app-error');

function createAuthController({ authService }) {
    return {
        login(req, res) {
            const { eml: email, pwd: password } = req.body ?? {};
            if (!email || !password || typeof email !== 'string' || typeof password !== 'string') {
                throw new AppError(400, 'Bad Request');
            }
            res.status(200).json({ token: authService.login({ email, password }) });
        },
    };
}

module.exports = { createAuthController };
