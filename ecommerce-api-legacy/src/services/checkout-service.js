const { AppError, failsWith } = require('../errors/app-error');
const { PAYMENT_STATUS } = require('../models/constants');

class CheckoutService {
    constructor({ courses, users, enrollments, payments, auditLogs, userService, gateway, runInTransaction, logger }) {
        Object.assign(this, { courses, users, enrollments, payments, auditLogs, userService, gateway, runInTransaction, logger });
    }

    // Every rejection happens before the first write; the writes then commit
    // or roll back together.
    checkout({ name, email, password, courseId, card }) {
        const course = this.#findCourse(courseId);

        const existing = failsWith('Erro DB', () => this.users.findByEmail(email));
        if (!existing) this.userService.assertCanCreateBuyer({ password });

        const status = this.gateway.authorize({ card, amount: course.price });
        if (status === PAYMENT_STATUS.DENIED) throw new AppError(400, 'Pagamento recusado');

        const { userId, enrollmentId } = this.runInTransaction(() => {
            const userId = this.userService.findOrCreateBuyer({ name, email, password });
            const enrollmentId = failsWith('Erro Matrícula', () => this.enrollments.create({ userId, courseId: course.id }));
            failsWith('Erro Pagamento', () => this.payments.create({ enrollmentId, amount: course.price, status }));
            failsWith('Erro DB', () => this.auditLogs.record(`Checkout curso ${course.id} por ${userId}`));
            return { userId, enrollmentId };
        });

        this.logger.info('checkout concluído', { userId, courseId: course.id, enrollmentId });
        return { enrollmentId };
    }

    #findCourse(courseId) {
        let course;
        try {
            course = this.courses.findActiveById(courseId);
        } catch (err) {
            throw new AppError(404, 'Curso não encontrado', { cause: err });
        }
        if (!course) throw new AppError(404, 'Curso não encontrado');
        return course;
    }
}

module.exports = { CheckoutService };
