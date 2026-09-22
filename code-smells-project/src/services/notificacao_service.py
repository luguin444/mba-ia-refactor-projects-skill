"""Efeitos externos do fluxo de pedido, isolados num ponto só.

Antes eram `print` disparados de dentro dos handlers HTTP. Continuam sendo simulação —
o que mudou é que agora existe um lugar único para trocá-los por integração real.
"""
import logging

from src.models.constants import StatusPedido

logger = logging.getLogger(__name__)


def notificar_pedido_criado(pedido_id: int, usuario_id: int) -> None:
    logger.info("notificando criação de pedido por email, sms e push",
                extra={"pedido_id": pedido_id, "usuario_id": usuario_id})


def notificar_mudanca_de_status(pedido_id: int, status: str) -> None:
    if status == StatusPedido.APROVADO:
        logger.info("pedido aprovado, preparar envio", extra={"pedido_id": pedido_id})
    elif status == StatusPedido.CANCELADO:
        logger.info("pedido cancelado, devolver estoque", extra={"pedido_id": pedido_id})
