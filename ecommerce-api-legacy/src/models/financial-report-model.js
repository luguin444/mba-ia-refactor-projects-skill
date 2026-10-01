// One row per (course, enrollment). Courses without enrollments come back
// with enrollment_id NULL; each enrollment is joined to its first payment.
const REPORT_ROWS = `
    SELECT c.id    AS course_id,
           c.title AS course_title,
           e.id    AS enrollment_id,
           u.id    AS user_id,
           u.name  AS user_name,
           p.id    AS payment_id,
           p.amount,
           p.status
      FROM courses c
      LEFT JOIN enrollments e ON e.course_id = c.id
      LEFT JOIN users u       ON u.id = e.user_id
      LEFT JOIN payments p    ON p.id = (SELECT MIN(id) FROM payments WHERE enrollment_id = e.id)
     ORDER BY c.id, e.id
`;

function createFinancialReportModel(db) {
    const rows = db.prepare(REPORT_ROWS);

    return {
        rows: () => rows.all(),
    };
}

module.exports = { createFinancialReportModel };
