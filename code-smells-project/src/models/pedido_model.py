"""Acesso a dados de pedido.

A listagem resolve pedido, itens e nome do produto num único JOIN — antes eram
1 + N + N*M queries com cursores numerados.
"""
import sqlite3

from src.database.connection import get_db
from src.models.serializers import serializar_item_pedido, serializar_pedido

_SELECT_PEDIDOS = """
    SELECT  p.id, p.usuario_id, p.status, p.total, p.criado_em,
            i.produto_id, i.quantidade, i.preco_unitario,
            pr.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido i ON i.pedido_id = p.id
    LEFT JOIN produtos    pr ON pr.id = i.produto_id
"""


def _agrupar(linhas: list[sqlite3.Row]) -> list[dict]:
    """Uma linha por item vira um pedido com a lista de itens, preservando a ordem."""
    pedidos: dict[int, dict] = {}
    for linha in linhas:
        pedido = pedidos.get(linha["id"])
        if pedido is None:
            pedido = pedidos[linha["id"]] = serializar_pedido(linha)
        if linha["produto_id"] is not None:
            pedido["itens"].append(serializar_item_pedido(linha))
    return list(pedidos.values())


def listar() -> list[dict]:
    linhas = get_db().execute(_SELECT_PEDIDOS + " ORDER BY p.id, i.id").fetchall()
    return _agrupar(linhas)


def listar_por_usuario(usuario_id: int) -> list[dict]:
    linhas = get_db().execute(
        _SELECT_PEDIDOS + " WHERE p.usuario_id = ? ORDER BY p.id, i.id", (usuario_id,)
    ).fetchall()
    return _agrupar(linhas)


def registrar(usuario_id: int, total: float, itens: list[dict]) -> int:
    """Grava pedido, itens e baixa de estoque numa transação única.

    Falha em qualquer ponto desfaz tudo — antes, três escritas relacionadas
    compartilhavam um commit no fim e nenhum caminho de erro chamava rollback.
    """
    conexao = get_db()
    try:
        conexao.execute("BEGIN")
        cursor = conexao.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
            (usuario_id, "pendente", total),
        )
        pedido_id = cursor.lastrowid

        for item in itens:
            conexao.execute(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario)"
                " VALUES (?, ?, ?, ?)",
                (pedido_id, item["produto_id"], item["quantidade"], item["preco_unitario"]),
            )
            conexao.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                (item["quantidade"], item["produto_id"]),
            )

        conexao.commit()
        return pedido_id
    except Exception:
        conexao.rollback()
        raise


def atualizar_status(pedido_id: int, novo_status: str) -> None:
    conexao = get_db()
    conexao.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
    conexao.commit()


def contar() -> int:
    return get_db().execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
