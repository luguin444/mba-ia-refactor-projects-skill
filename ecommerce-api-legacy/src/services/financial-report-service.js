const { PAYMENT_STATUS } = require('./payment-service');

const UNKNOWN_STUDENT = 'Unknown';

// Agrega as linhas do relatório. A regra "só pagamento PAID entra no faturamento"
// vivia dentro do handler HTTP do relatório (AP-09); agora é uma função pura sobre
// as linhas, testável sem banco e sem servidor.
class FinancialReportService {
    constructor({ financialReportModel }) {
        this.financialReportModel = financialReportModel;
    }

    async build() {
        const rows = await this.financialReportModel.findCourseEnrollmentRows();
        return this.#groupByCourse(rows);
    }

    #groupByCourse(rows) {
        const byCourseId = new Map();

        for (const row of rows) {
            if (!byCourseId.has(row.course_id)) {
                byCourseId.set(row.course_id, {
                    course: row.course_title,
                    revenue: 0,
                    students: [],
                });
            }

            // LEFT JOIN: curso sem matrícula produz uma linha com enrollment_id nulo.
            // Ele entra no relatório com faturamento zero e nenhum aluno.
            if (row.enrollment_id === null) continue;

            const courseData = byCourseId.get(row.course_id);

            if (row.payment_status === PAYMENT_STATUS.PAID) {
                courseData.revenue += row.payment_amount;
            }

            courseData.students.push({
                // Usuário removido deixa a matrícula apontando para ninguém — o
                // relatório continua mostrando 'Unknown', como antes (ver AP-24).
                student: row.student_name ?? UNKNOWN_STUDENT,
                paid: row.payment_amount ?? 0,
            });
        }

        return [...byCourseId.values()];
    }
}

module.exports = FinancialReportService;
