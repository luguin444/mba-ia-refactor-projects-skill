const { Router } = require('express');

// Public on purpose: checkout is the only way an account gets created.
function checkoutRoutes({ checkoutController }) {
    const router = Router();
    router.post('/checkout', checkoutController.checkout);
    return router;
}

module.exports = { checkoutRoutes };
