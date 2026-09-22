// A mensagem é literalmente a do projeto original, incluindo a admissão de que
// matrículas e pagamentos ficam órfãos. É o corpo que o baseline capturou, tanto
// para id existente quanto inexistente, e preservá-lo é preservar o contrato.
// A limpeza em cascata (AP-24) está descrita em src/database/schema.js e depende
// de decisão humana, porque mudaria o relatório financeiro após o delete.
const DELETE_MESSAGE = 'Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.';

class UserController {
    constructor({ userService }) {
        this.userService = userService;
        this.destroy = this.destroy.bind(this);
    }

    async destroy(req, res) {
        await this.userService.deleteById(req.params.id);
        return res.send(DELETE_MESSAGE);
    }
}

module.exports = UserController;
module.exports.DELETE_MESSAGE = DELETE_MESSAGE;
