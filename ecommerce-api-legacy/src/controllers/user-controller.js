// The message admits the orphaned rows; it is the current contract and stays
// until the cascade behavior is decided (AP-24).
const DELETED_MESSAGE = 'Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.';

function createUserController({ userService }) {
    return {
        remove(req, res) {
            userService.remove(req.params.id);
            res.send(DELETED_MESSAGE);
        },
    };
}

module.exports = { createUserController };
