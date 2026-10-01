const { checkoutRoutes } = require('./checkout-routes');
const { authRoutes } = require('./auth-routes');
const { financialReportRoutes } = require('./financial-report-routes');
const { userRoutes } = require('./user-routes');

function registerRoutes(app, deps) {
    app.use('/api', checkoutRoutes(deps));
    app.use('/api', authRoutes(deps));
    app.use('/api', financialReportRoutes(deps));
    app.use('/api', userRoutes(deps));
}

module.exports = { registerRoutes };
