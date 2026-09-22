// Express 4 não captura rejeição de handler async: sem isto, um `await` que
// falha vira unhandled rejection e a requisição fica pendurada até o timeout.
// Com isto, todo erro chega ao middleware central (AP-15).

const asyncHandler = (handler) => (req, res, next) => {
    Promise.resolve(handler(req, res, next)).catch(next);
};

module.exports = asyncHandler;
