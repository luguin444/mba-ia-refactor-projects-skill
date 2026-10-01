const { AppError } = require('../errors/app-error');
const { USER_ROLE } = require('../models/constants');

// Routes declare which level they require; only this module knows how to
// read and verify the credential. Verified claims land on req.auth.
function createAuthMiddleware({ tokens }) {
    const requerAutenticacao = (req, res, next) => {
        const header = req.get('Authorization') || '';
        if (!header.startsWith('Bearer ')) return next(new AppError(401, 'Unauthorized'));
        try {
            req.auth = tokens.verify(header.slice('Bearer '.length));
        } catch (err) {
            return next(new AppError(401, 'Unauthorized', { cause: err }));
        }
        next();
    };

    const requerAdmin = [requerAutenticacao, (req, res, next) => {
        next(req.auth.role === USER_ROLE.ADMIN ? undefined : new AppError(403, 'Forbidden'));
    }];

    // The subject id in the path must be the caller's own, unless the caller is admin.
    const requerDonoOuAdmin = (param) => [requerAutenticacao, (req, res, next) => {
        const allowed = req.auth.role === USER_ROLE.ADMIN || String(req.params[param]) === req.auth.sub;
        next(allowed ? undefined : new AppError(403, 'Forbidden'));
    }];

    return { requerAutenticacao, requerAdmin, requerDonoOuAdmin };
}

module.exports = { createAuthMiddleware };
