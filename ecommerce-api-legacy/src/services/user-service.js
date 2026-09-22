// Operações de usuário que não pertencem ao fluxo de checkout.
class UserService {
    constructor({ userModel }) {
        this.userModel = userModel;
    }

    // Devolve quantas linhas saíram. O controller ignora o número para preservar
    // o contrato — id inexistente respondia 200 no original e continua respondendo
    // —, mas a informação existe para quando a resposta puder mudar.
    deleteById(id) {
        return this.userModel.deleteById(id);
    }
}

module.exports = UserService;
