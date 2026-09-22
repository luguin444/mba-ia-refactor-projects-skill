const express = require('express');

const asyncHandler = require('../middlewares/async-handler');

// Montado em /api/users: o caminho final é DELETE /api/users/:id.
function createUserRoutes({ userController }) {
    const router = express.Router();
    router.delete('/:id', asyncHandler(userController.destroy));
    return router;
}

module.exports = createUserRoutes;
