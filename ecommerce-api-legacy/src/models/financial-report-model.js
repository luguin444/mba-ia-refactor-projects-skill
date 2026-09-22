// Leitura agregada do relatório financeiro.
//
// Substitui as 1 + N + 2*N consultas em laço do código original por uma só (AP-17).
// A subconsulta em `payments` reproduz de propósito a semântica do `db.get`
// anterior — quando uma matrícula tem mais de um pagamento, só o primeiro conta.
const REPORT_QUERY = `
    SELECT c.id       AS course_id,
           c.title    AS course_title,
           e.id       AS enrollment_id,
           u.name     AS student_name,
           p.amount   AS payment_amount,
           p.status   AS payment_status
    FROM courses c
    LEFT JOIN enrollments e ON e.course_id = c.id
    LEFT JOIN users u       ON u.id = e.user_id
    LEFT JOIN payments p    ON p.id = (
        SELECT MIN(inner_p.id) FROM payments inner_p WHERE inner_p.enrollment_id = e.id
    )
    ORDER BY c.id, e.id
`;

class FinancialReportModel {
    constructor(db) {
        this.db = db;
    }

    // Ordem vinda do ORDER BY, não do escalonamento dos callbacks (AP-18).
    findCourseEnrollmentRows() {
        return this.db.all(REPORT_QUERY);
    }
}

module.exports = FinancialReportModel;
