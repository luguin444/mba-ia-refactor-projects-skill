const { PAYMENT_STATUS } = require('../models/constants');

// STUB: this project integrates no real payment gateway. Any card starting
// with this prefix is approved and nothing is charged. Choosing the real
// gateway is a pending product decision (AP-33); swapping this class is the
// only change the rest of the code needs.
const STUB_APPROVED_CARD_PREFIX = '4';

class StubPaymentGateway {
    constructor({ gatewayKey, logger }) {
        this.gatewayKey = gatewayKey;
        this.logger = logger;
        logger.warn('autorização de pagamento em modo STUB: cartões com prefixo "4" são aprovados sem cobrança', {
            gatewayKeyConfigured: Boolean(gatewayKey),
        });
    }

    authorize({ card, amount }) {
        this.logger.info('processando pagamento', { card: `****${card.slice(-4)}`, amount });
        return card.startsWith(STUB_APPROVED_CARD_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
    }
}

module.exports = { StubPaymentGateway };
