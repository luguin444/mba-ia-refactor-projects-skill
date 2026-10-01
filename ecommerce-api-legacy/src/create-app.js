const express = require('express');

const { openDatabase } = require('./config/database');
const { createSchema } = require('./database/schema');
const { seedExampleData } = require('./database/seed');
const { provisionAdmin } = require('./database/provision-admin');

const { createUserModel } = require('./models/user-model');
const { createCourseModel } = require('./models/course-model');
const { createEnrollmentModel } = require('./models/enrollment-model');
const { createPaymentModel } = require('./models/payment-model');
const { createAuditLogModel } = require('./models/audit-log-model');
const { createFinancialReportModel } = require('./models/financial-report-model');

const { StubPaymentGateway } = require('./services/payment-gateway');
const { TokenService } = require('./services/token-service');
const { UserService } = require('./services/user-service');
const { AuthService } = require('./services/auth-service');
const { CheckoutService } = require('./services/checkout-service');
const { FinancialReportService } = require('./services/financial-report-service');

const { createCheckoutController } = require('./controllers/checkout-controller');
const { createAuthController } = require('./controllers/auth-controller');
const { createFinancialReportController } = require('./controllers/financial-report-controller');
const { createUserController } = require('./controllers/user-controller');

const { createAuthMiddleware } = require('./middlewares/auth');
const { createErrorHandler } = require('./middlewares/error-handler');
const { registerRoutes } = require('./routes');

// Composition root: builds every dependency from config and wires the app.
function createApp({ env, logger }) {
    const db = openDatabase(env.dbPath);
    createSchema(db);
    if (env.seedOnBoot) seedExampleData(db);
    provisionAdmin(db, env, logger);

    const users = createUserModel(db);
    const tokens = new TokenService({ secret: env.jwtSecret });
    const userService = new UserService({ users });

    const checkoutService = new CheckoutService({
        courses: createCourseModel(db),
        users,
        enrollments: createEnrollmentModel(db),
        payments: createPaymentModel(db),
        auditLogs: createAuditLogModel(db),
        userService,
        gateway: new StubPaymentGateway({ gatewayKey: env.paymentGatewayKey, logger }),
        runInTransaction: (work) => db.transaction(work)(),
        logger,
    });
    const authService = new AuthService({ users, tokens });
    const financialReportService = new FinancialReportService({ financialReports: createFinancialReportModel(db) });

    const app = express();
    app.use(express.json());
    registerRoutes(app, {
        auth: createAuthMiddleware({ tokens }),
        checkoutController: createCheckoutController({ checkoutService }),
        authController: createAuthController({ authService }),
        financialReportController: createFinancialReportController({ financialReportService }),
        userController: createUserController({ userService }),
    });
    app.use(createErrorHandler({ logger }));

    return app;
}

module.exports = { createApp };
