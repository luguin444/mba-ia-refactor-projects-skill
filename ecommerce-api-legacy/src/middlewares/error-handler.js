const AppError = require('../errors/app-error');

// Substitui os seis blocos de tratamento repetidos nos handlers (AP-15, AP-21).
//
// O corpo continua sendo texto puro via `res.send`, e não JSON: o baseline
// registrou `text/html` em toda resposta de erro do projeto original, e mudar
// isso quebraria o contrato tanto quanto mudar o status code.
function createErrorHandler({ logger }) {
    return function errorHandler(err, req, res, _next) {
        if (err instanceof AppError) {
            logger.warn('requisição rejeitada', {
                method: req.method,
                path: req.path,
                status: err.status,
                message: err.message,
            });
            return res.status(err.status).send(err.message);
        }

        // Inclui o SyntaxError que o express.json lança em corpo malformado.
        // Antes, esse caminho devolvia o stack trace do Express em HTML, com o
        // caminho absoluto do projeto no sistema de arquivos.
        const status = Number.isInteger(err.status) ? err.status : 500;
        logger.error('erro não tratado', {
            method: req.method,
            path: req.path,
            status,
            error: err.message,
            stack: err.stack,
        });

        return res.status(status).send('Erro interno');
    };
}

module.exports = createErrorHandler;
