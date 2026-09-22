const { randomBytes } = require('node:crypto');

const AppError = require('../errors/app-error');
const { PAYMENT_STATUS } = require('./payment-service');

// Orquestra o checkout: curso, usuário, autorização, matrícula, pagamento e
// auditoria. Atravessa cinco entidades, que é o critério para existir um service
// em vez de deixar a regra no controller.
class CheckoutService {
    constructor({
        db,
        userModel,
        courseModel,
        enrollmentModel,
        paymentModel,
        auditLogModel,
        paymentService,
        passwordService,
    }) {
        this.db = db;
        this.userModel = userModel;
        this.courseModel = courseModel;
        this.enrollmentModel = enrollmentModel;
        this.paymentModel = paymentModel;
        this.auditLogModel = auditLogModel;
        this.paymentService = paymentService;
        this.passwordService = passwordService;
    }

    async execute({ name, email, password, courseId, cardNumber }) {
        const course = await this.courseModel.findActiveById(courseId);
        if (!course) throw new AppError('Curso não encontrado', 404);

        // Autorizar antes de escrever qualquer coisa. No código original o usuário
        // era criado primeiro e só depois o pagamento era avaliado, de modo que um
        // cartão recusado deixava uma conta órfã para trás (AP-12).
        const status = this.paymentService.authorize({ cardNumber });
        if (status === PAYMENT_STATUS.DENIED) throw new AppError('Pagamento recusado', 400);

        // As quatro escritas abaixo eram callbacks encadeados sem transação: uma
        // falha no meio deixava matrícula sem pagamento (AP-10).
        return this.db.transaction(async () => {
            const userId = await this.#findOrCreateUser({ name, email, password });
            const enrollmentId = await this.enrollmentModel.create({ userId, courseId });

            await this.paymentModel.create({
                enrollmentId,
                amount: course.price,
                status,
            });
            await this.auditLogModel.record(`Checkout curso ${courseId} por ${userId}`);

            return { enrollmentId };
        });
    }

    async #findOrCreateUser({ name, email, password }) {
        const existing = await this.userModel.findByEmail(email);
        if (existing) return existing.id;

        // O checkout continua criando a conta silenciosamente — isso é contrato,
        // a requisição sem senha responde 200 e o baseline registra isso. O que
        // muda é a senha: era o literal "123456" para todo mundo que omitisse o
        // campo, e passa a ser aleatória, inutilizável por quem adivinhar o
        // padrão. Recuperá-la exige um fluxo de redefinição, que não existe aqui.
        const effectivePassword = password || randomBytes(32).toString('hex');
        const passwordHash = await this.passwordService.hash(effectivePassword);

        return this.userModel.create({ name, email, passwordHash });
    }
}

module.exports = CheckoutService;
