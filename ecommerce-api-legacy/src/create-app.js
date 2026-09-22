const express = require('express');

const registerRoutes = require('./routes');
const createErrorHandler = require('./middlewares/error-handler');

const UserModel = require('./models/user-model');
const CourseModel = require('./models/course-model');
const EnrollmentModel = require('./models/enrollment-model');
const PaymentModel = require('./models/payment-model');
const AuditLogModel = require('./models/audit-log-model');
const FinancialReportModel = require('./models/financial-report-model');

const PasswordService = require('./services/password-service');
const PaymentService = require('./services/payment-service');
const CheckoutService = require('./services/checkout-service');
const FinancialReportService = require('./services/financial-report-service');
const UserService = require('./services/user-service');

const CheckoutController = require('./controllers/checkout-controller');
const FinancialReportController = require('./controllers/financial-report-controller');
const UserController = require('./controllers/user-controller');

// Monta o grafo de dependências e devolve a app pronta. Nada aqui abre conexão
// nem decide regra: só liga as peças. Separado do entry point para que um teste
// possa montar a app sobre um banco próprio sem subir servidor.
function buildDependencies({ db, config, logger }) {
    const passwordService = new PasswordService();

    const models = {
        userModel: new UserModel(db),
        courseModel: new CourseModel(db),
        enrollmentModel: new EnrollmentModel(db),
        paymentModel: new PaymentModel(db),
        auditLogModel: new AuditLogModel(db),
        financialReportModel: new FinancialReportModel(db),
    };

    const paymentService = new PaymentService({
        gatewayKey: config.paymentGatewayKey,
        logger,
    });

    const services = {
        passwordService,
        paymentService,
        checkoutService: new CheckoutService({ db, ...models, paymentService, passwordService }),
        financialReportService: new FinancialReportService(models),
        userService: new UserService(models),
    };

    const controllers = {
        checkoutController: new CheckoutController(services),
        financialReportController: new FinancialReportController(services),
        userController: new UserController(services),
    };

    return { models, services, controllers };
}

function createApp({ db, config, logger }) {
    const { controllers, services } = buildDependencies({ db, config, logger });

    const app = express();
    app.use(express.json());

    registerRoutes(app, controllers);

    // Último a ser registrado: só assim o Express o reconhece como middleware
    // de erro e ele alcança tudo o que veio antes, inclusive o express.json.
    app.use(createErrorHandler({ logger }));

    return { app, services };
}

module.exports = createApp;
