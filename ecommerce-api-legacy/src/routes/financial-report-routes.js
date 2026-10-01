const { Router } = require('express');

// Admin: the report names every student and what each one paid.
function financialReportRoutes({ financialReportController, auth }) {
    const router = Router();
    router.get('/admin/financial-report', auth.requerAdmin, financialReportController.show);
    return router;
}

module.exports = { financialReportRoutes };
