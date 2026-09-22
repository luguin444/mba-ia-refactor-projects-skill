const express = require('express');

const asyncHandler = require('../middlewares/async-handler');

// Montado em /api/admin: o caminho final é GET /api/admin/financial-report.
// A rota segue sem autenticação, como no original — ver AP-07 no relatório de
// auditoria, marcado REQUER DECISÃO DE PRODUTO.
function createFinancialReportRoutes({ financialReportController }) {
    const router = express.Router();
    router.get('/financial-report', asyncHandler(financialReportController.show));
    return router;
}

module.exports = createFinancialReportRoutes;
