const PAYMENT_STATUS = Object.freeze({
    PAID: 'PAID',
    DENIED: 'DENIED',
});

// O código original aprovava o pagamento com `cc.startsWith("4")`, um caractere
// solto no meio de um ternário dentro do handler HTTP (AP-09, AP-27).
// A regra continua sendo a mesma — é um stub, não uma integração — mas agora
// tem nome, fica isolada do transporte e é testável sem subir servidor.
const APPROVED_CARD_PREFIX = '4';

class PaymentService {
    constructor({ gatewayKey = null, logger }) {
        this.gatewayKey = gatewayKey;
        this.logger = logger;

        if (!this.gatewayKey) {
            this.logger.warn(
                'PAYMENT_GATEWAY_KEY ausente: autorização de pagamento rodando em modo stub',
            );
        }
    }

    authorize({ cardNumber }) {
        // O log original imprimia o cartão inteiro e a chave do gateway (AP-04).
        // Sobra o que serve para rastrear sem vazar: os quatro últimos dígitos.
        this.logger.info('processando pagamento', { last4: String(cardNumber).slice(-4) });

        return String(cardNumber).startsWith(APPROVED_CARD_PREFIX)
            ? PAYMENT_STATUS.PAID
            : PAYMENT_STATUS.DENIED;
    }
}

module.exports = PaymentService;
module.exports.PAYMENT_STATUS = PAYMENT_STATUS;
