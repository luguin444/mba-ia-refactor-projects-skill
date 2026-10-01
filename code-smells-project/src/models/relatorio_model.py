from src.database.connection import get_db
from src.models.constants import StatusPedido


def totais_de_vendas():
    row = get_db().execute(
        """
        SELECT COUNT(*)                                  AS total_pedidos,
               COALESCE(SUM(total), 0)                   AS faturamento,
               COALESCE(SUM(status = ?), 0)              AS pendentes,
               COALESCE(SUM(status = ?), 0)              AS aprovados,
               COALESCE(SUM(status = ?), 0)              AS cancelados
        FROM pedidos
        """,
        (StatusPedido.PENDENTE, StatusPedido.APROVADO, StatusPedido.CANCELADO),
    ).fetchone()
    return dict(row)
