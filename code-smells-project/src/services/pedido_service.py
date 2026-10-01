import logging

from src.database.connection import transacao
from src.errors import ValidacaoError
from src.models import pedido_model, produto_model, usuario_model
from src.models.constants import StatusPedido

logger = logging.getLogger(__name__)

_notificador = None


def configurar_notificacao(notificador):
    """Chamado uma vez pelo composition root."""
    global _notificador
    _notificador = notificador


class _RegraDePedido(ValidacaoError):
    """Recusa por regra de pedido: o corpo leva `"sucesso": false`, como no contrato original."""

    def __init__(self, mensagem):
        super().__init__(mensagem, com_sucesso=True)


def _quantidade_valida(valor):
    return isinstance(valor, int) and not isinstance(valor, bool) and valor > 0


def validar(dados):
    if not dados or not isinstance(dados, dict):
        raise ValidacaoError("Dados inválidos")

    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])
    if not usuario_id:
        raise ValidacaoError("Usuario ID é obrigatório")
    if not itens:
        raise ValidacaoError("Pedido deve ter pelo menos 1 item")
    if not isinstance(itens, list):
        raise ValidacaoError("Itens devem ser uma lista")
    for item in itens:
        if not isinstance(item, dict) or item.get("produto_id") is None:
            raise ValidacaoError("Todo item precisa de produto_id")
        if not _quantidade_valida(item.get("quantidade")):
            raise ValidacaoError("Quantidade deve ser um inteiro positivo")
    return usuario_id, itens


def criar(usuario_id, itens):
    """Recebe dados já validados e com dono já verificado."""
    if not usuario_model.existe(usuario_id):
        raise ValidacaoError("Usuário não encontrado")

    total = 0
    precos = {}
    for item in itens:
        produto = produto_model.buscar_por_id(item["produto_id"])
        if produto is None:
            raise _RegraDePedido(f"Produto {item['produto_id']} não encontrado")
        if produto["estoque"] < item["quantidade"]:
            raise _RegraDePedido(f"Estoque insuficiente para {produto['nome']}")
        precos[item["produto_id"]] = produto
        total = total + (produto["preco"] * item["quantidade"])

    with transacao() as conexao:
        pedido_id = pedido_model.inserir(conexao, usuario_id, total)
        for item in itens:
            produto = precos[item["produto_id"]]
            pedido_model.inserir_item(conexao, pedido_id, item["produto_id"], item["quantidade"], produto["preco"])
            if not produto_model.debitar_estoque(conexao, item["produto_id"], item["quantidade"]):
                raise _RegraDePedido(f"Estoque insuficiente para {produto['nome']}")

    logger.info("pedido criado id=%s usuario=%s", pedido_id, usuario_id)
    _notificador.pedido_criado(pedido_id, usuario_id)
    return {"pedido_id": pedido_id, "total": total}


def listar(limite=None, offset=0):
    return pedido_model.listar(limite, offset)


def listar_por_usuario(usuario_id, limite=None, offset=0):
    return pedido_model.listar_por_usuario(usuario_id, limite, offset)


def atualizar_status(pedido_id, dados):
    dados = dados if isinstance(dados, dict) else {}
    novo_status = dados.get("status", "")
    if novo_status not in list(StatusPedido):
        raise ValidacaoError("Status inválido")

    pedido_model.atualizar_status(pedido_id, novo_status)

    if novo_status == StatusPedido.APROVADO:
        _notificador.pedido_aprovado(pedido_id)
    elif novo_status == StatusPedido.CANCELADO:
        _notificador.pedido_cancelado(pedido_id)
