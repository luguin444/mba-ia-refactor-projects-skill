const { AppError } = require('../errors/app-error');

const isNumericId = (value) => typeof value === 'number'
    || (typeof value === 'string' && value.trim() !== '' && Number.isFinite(Number(value)));

// Public field names (usr, eml, pwd, c_id, card) are the API contract.
function readCheckoutInput(body = {}) {
    const { usr: name, eml: email, pwd: password, c_id: courseId, card } = body;

    if (!name || !email || !courseId || !card) throw new AppError(400, 'Bad Request');
    if (typeof name !== 'string' || typeof email !== 'string' || typeof card !== 'string' || !isNumericId(courseId)) {
        throw new AppError(400, 'Bad Request');
    }
    return { name, email, password, courseId, card };
}

function createCheckoutController({ checkoutService }) {
    return {
        checkout(req, res) {
            const { enrollmentId } = checkoutService.checkout(readCheckoutInput(req.body));
            res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
        },
    };
}

module.exports = { createCheckoutController };
