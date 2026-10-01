import logging

logger = logging.getLogger(__name__)


class NotificacaoService:
    """STUB: este projeto não integra provedor de e-mail, SMS ou push.

    Cada envio é só uma linha de log. Escolher o provedor é decisão de produto
    (relatório de auditoria, AP-33); quando existir, troca-se esta classe.
    """

    def __init__(self):
        logger.warning("Nenhum provedor de notificação configurado: e-mail, SMS e push rodam em modo stub (só log)")

    def pedido_criado(self, pedido_id, usuario_id):
        logger.info("[stub] e-mail: pedido %s criado para usuario %s", pedido_id, usuario_id)
        logger.info("[stub] sms: seu pedido foi recebido")
        logger.info("[stub] push: novo pedido recebido pelo sistema")

    def pedido_aprovado(self, pedido_id):
        logger.info("[stub] notificação: pedido %s aprovado, preparar envio", pedido_id)

    def pedido_cancelado(self, pedido_id):
        # A devolução de estoque anunciada aqui no código original nunca aconteceu;
        # se o cancelamento deve repor estoque é decisão de produto (AP-33).
        logger.info("[stub] notificação: pedido %s cancelado", pedido_id)
