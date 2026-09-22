const createCheckoutRoutes = require('./checkout-routes');
const createFinancialReportRoutes = require('./financial-report-routes');
const createUserRoutes = require('./user-routes');

// Único lugar que decide prefixo. Os três caminhos finais são exatamente os do
// projeto original: POST /api/checkout, GET /api/admin/financial-report e
// DELETE /api/users/:id.
function registerRoutes(app, controllers) {
    app.use('/api', createCheckoutRoutes(controllers));
    app.use('/api/admin', createFinancialReportRoutes(controllers));
    app.use('/api/users', createUserRoutes(controllers));
}

module.exports = registerRoutes;
