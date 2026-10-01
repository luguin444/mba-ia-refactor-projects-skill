const { Router } = require('express');

// Public: issues the credential.
function authRoutes({ authController }) {
    const router = Router();
    router.post('/login', authController.login);
    return router;
}

module.exports = { authRoutes };
