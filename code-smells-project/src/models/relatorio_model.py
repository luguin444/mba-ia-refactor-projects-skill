"""Agregações de vendas. Só devolve números crus — a política de desconto vive no serviço."""
from src.database.connection import get_db


def agregar_vendas() -> dict:
    """Totais e contagem por status numa única varredura, em vez de cinco COUNT separados."""
    linha = get_db().execute(
        """
        SELECT COUNT(*)                                          AS total_pedidos,
               COALESCE(SUM(total), 0)                           AS faturamento,
               SUM(CASE WHEN status = 'pendente'  THEN 1 ELSE 0 END) AS pendentes,
               SUM(CASE WHEN status = 'aprovado'  THEN 1 ELSE 0 END) AS aprovados,
               SUM(CASE WHEN status = 'cancelado' THEN 1 ELSE 0 END) AS cancelados
        FROM pedidos
        """
    ).fetchone()

    return {
        "total_pedidos": linha["total_pedidos"],
        "faturamento": linha["faturamento"],
        "pendentes": linha["pendentes"] or 0,
        "aprovados": linha["aprovados"] or 0,
        "cancelados": linha["cancelados"] or 0,
    }
