"""Regra de negócio de pedido: disponibilidade, total e transição de status.

O cálculo do total e a checagem de estoque saíram da camada de dados; a validação
de status e o disparo de notificação saíram do controller.
"""
import logging

from src.middlewares.error_handler import AppError
from src.models import pedido_model, produto_model
from src.models.constants import STATUS_VALIDOS
from src.services import notificacao_service

logger = logging.getLogger(__name__)


def listar() -> list[dict]:
    return pedido_model.listar()


def listar_por_usuario(usuario_id: int) -> list[dict]:
    return pedido_model.listar_por_usuario(usuario_id)


def _montar_itens(itens_solicitados: list[dict]) -> tuple[list[dict], float]:
    """Resolve preço e disponibilidade de cada item e devolve os itens com o total."""
    itens, total = [], 0.0

    for solicitado in itens_solicitados:
        produto = produto_model.buscar_por_id(solicitado["produto_id"])
        if produto is None:
            raise AppError(f"Produto {solicitado['produto_id']} não encontrado", incluir_sucesso=True)
        if produto["estoque"] < solicitado["quantidade"]:
            raise AppError(f"Estoque insuficiente para {produto['nome']}", incluir_sucesso=True)

        total += produto["preco"] * solicitado["quantidade"]
        itens.append({
            "produto_id": produto["id"],
            "quantidade": solicitado["quantidade"],
            "preco_unitario": produto["preco"],
        })

    return itens, total


def criar(dados: dict | None) -> dict:
    if not dados:
        raise AppError("Dados inválidos")

    usuario_id = dados.get("usuario_id")
    itens_solicitados = dados.get("itens", [])

    if not usuario_id:
        raise AppError("Usuario ID é obrigatório")
    if not itens_solicitados:
        raise AppError("Pedido deve ter pelo menos 1 item")

    itens, total = _montar_itens(itens_solicitados)
    pedido_id = pedido_model.registrar(usuario_id, total, itens)

    notificacao_service.notificar_pedido_criado(pedido_id, usuario_id)
    return {"pedido_id": pedido_id, "total": total}


def atualizar_status(pedido_id: int, dados: dict | None) -> None:
    novo_status = (dados or {}).get("status", "")
    if novo_status not in STATUS_VALIDOS:
        raise AppError("Status inválido")

    pedido_model.atualizar_status(pedido_id, novo_status)
    notificacao_service.notificar_mudanca_de_status(pedido_id, novo_status)
