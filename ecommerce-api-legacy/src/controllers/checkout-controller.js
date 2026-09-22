const AppError = require('../errors/app-error');

// `usr`, `eml`, `pwd`, `c_id` e `card` são contrato público da API: os nomes das
// chaves ficam como estão. O que some são as variáveis `u`, `e`, `p`, `cid`, `cc`
// de uma letra que carregavam esses valores adiante (AP-29).
function parseCheckoutRequest(body = {}) {
    return {
        name: body.usr,
        email: body.eml,
        password: body.pwd,
        courseId: body.c_id,
        cardNumber: body.card,
    };
}

class CheckoutController {
    constructor({ checkoutService }) {
        this.checkoutService = checkoutService;
        this.create = this.create.bind(this);
    }

    async create(req, res) {
        const input = parseCheckoutRequest(req.body);

        // Mesma condição do original, inclusive a ausência de `password`:
        // a senha nunca foi obrigatória neste endpoint.
        if (!input.name || !input.email || !input.courseId || !input.cardNumber) {
            throw new AppError('Bad Request', 400);
        }

        const { enrollmentId } = await this.checkoutService.execute(input);

        return res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
    }
}

module.exports = CheckoutController;
