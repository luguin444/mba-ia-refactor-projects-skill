function createFinancialReportController({ financialReportService }) {
    return {
        show(req, res) {
            res.json(financialReportService.build());
        },
    };
}

module.exports = { createFinancialReportController };
