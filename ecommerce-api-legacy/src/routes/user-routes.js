const { Router } = require('express');

// Owner or admin: subject id in the path, destructive write.
function userRoutes({ userController, auth }) {
    const router = Router();
    router.delete('/users/:id', auth.requerDonoOuAdmin('id'), userController.remove);
    return router;
}

module.exports = { userRoutes };
