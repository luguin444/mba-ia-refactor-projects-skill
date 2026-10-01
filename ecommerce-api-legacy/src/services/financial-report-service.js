const { failsWith } = require('../errors/app-error');
const { PAYMENT_STATUS } = require('../models/constants');

const UNKNOWN_STUDENT = 'Unknown';

class FinancialReportService {
    constructor({ financialReports }) {
        this.financialReports = financialReports;
    }

    // Revenue counts only PAID payments; `paid` shows the amount of the
    // enrollment's payment whatever its status, or 0 when there is none.
    build() {
        const rows = failsWith('Erro DB', () => this.financialReports.rows());
        const byCourse = new Map();

        for (const row of rows) {
            if (!byCourse.has(row.course_id)) {
                byCourse.set(row.course_id, { course: row.course_title, revenue: 0, students: [] });
            }
            if (row.enrollment_id === null) continue;

            const entry = byCourse.get(row.course_id);
            if (row.status === PAYMENT_STATUS.PAID) entry.revenue += row.amount;
            entry.students.push({
                student: row.user_id === null ? UNKNOWN_STUDENT : row.user_name,
                paid: row.payment_id === null ? 0 : row.amount,
            });
        }

        return [...byCourse.values()];
    }
}

module.exports = { FinancialReportService };
