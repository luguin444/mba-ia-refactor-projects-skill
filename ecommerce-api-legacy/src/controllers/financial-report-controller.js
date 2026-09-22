class FinancialReportController {
    constructor({ financialReportService }) {
        this.financialReportService = financialReportService;
        this.show = this.show.bind(this);
    }

    async show(req, res) {
        const report = await this.financialReportService.build();
        return res.json(report);
    }
}

module.exports = FinancialReportController;
