const { randomBytes } = require('node:crypto');

const DEFAULT_PORT = 3000;

// Without JWT_SECRET the process generates an ephemeral secret and warns:
// every issued token stops validating on restart.
function jwtSecret(logger) {
    if (process.env.JWT_SECRET) return process.env.JWT_SECRET;
    logger.warn('JWT_SECRET ausente: usando segredo efêmero gerado no boot. Tokens não sobrevivem ao restart. Defina JWT_SECRET em produção.');
    return randomBytes(32).toString('hex');
}

function loadEnv(logger) {
    return {
        port: Number(process.env.PORT) || DEFAULT_PORT,
        dbPath: process.env.DB_PATH || ':memory:',
        seedOnBoot: (process.env.SEED_ON_BOOT ?? 'true').toLowerCase() !== 'false',
        paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || null,
        jwtSecret: jwtSecret(logger),
        adminEmail: process.env.ADMIN_EMAIL || null,
        adminPassword: process.env.ADMIN_PASSWORD || null,
    };
}

module.exports = { loadEnv };
