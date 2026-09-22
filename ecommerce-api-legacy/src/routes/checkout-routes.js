const express = require('express');

const asyncHandler = require('../middlewares/async-handler');

// Montado em /api pelo agregador: o caminho final é POST /api/checkout.
function createCheckoutRoutes({ checkoutController }) {
    const router = express.Router();
    router.post('/checkout', asyncHandler(checkoutController.create));
    return router;
}

module.exports = createCheckoutRoutes;
