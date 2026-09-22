// Único lugar do projeto que lê variáveis de ambiente.
// Nenhum valor sensível tem default: um segredo com fallback no código é o
// mesmo segredo hardcoded com uma indireção a mais (AP-03).

function optionalInt(name, fallback) {
    const raw = process.env[name];
    if (raw === undefined || raw === '') return fallback;
    const parsed = Number.parseInt(raw, 10);
    if (Number.isNaN(parsed)) {
        throw new Error(`Variável de ambiente ${name} precisa ser um inteiro, recebido: ${raw}`);
    }
    return parsed;
}

const nodeEnv = process.env.NODE_ENV || 'development';

const config = {
    nodeEnv,
    isProduction: nodeEnv === 'production',
    port: optionalInt('PORT', 3000),
    logLevel: process.env.LOG_LEVEL || 'info',

    // Sem default. Ausente, o gateway roda em modo stub e o PaymentService avisa.
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || null,
};

module.exports = config;
