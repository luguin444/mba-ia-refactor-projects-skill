const { STATUS_CODES } = require('node:http');
const { AppError } = require('../errors/app-error');

// Error bodies are plain text, as in the original API. Stack traces go to
// the log only, never to the client.
function createErrorHandler({ logger }) {
    // Express recognizes an error handler by its four parameters.
    return (err, req, res, _next) => {
        if (err instanceof AppError) {
            if (err.status >= 500) logger.error(err.message, { path: req.path, cause: err.cause?.stack });
            return res.status(err.status).send(err.message);
        }

        // body-parser errors (malformed JSON, payload too large) carry a client status.
        if (err.expose && err.status >= 400 && err.status < 500) {
            logger.warn('requisição rejeitada', { path: req.path, status: err.status, reason: err.message });
            return res.status(err.status).send(STATUS_CODES[err.status]);
        }

        logger.error('erro não tratado', { path: req.path, stack: err.stack });
        res.status(500).send('Erro interno');
    };
}

module.exports = { createErrorHandler };
