from src.database.connection import get_db, transacao
from src.database.paginacao import aplicar_limite
from src.models import serializers


def listar(limite=None, offset=0):
    sql, params = aplicar_limite("SELECT * FROM produtos ORDER BY id", [], limite, offset)
    return [serializers.produto(row) for row in get_db().execute(sql, params).fetchall()]


def buscar_por_id(produto_id):
    row = get_db().execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
    return serializers.produto(row) if row else None


def buscar(termo, categoria=None, preco_min=None, preco_max=None):
    sql, params = "SELECT * FROM produtos WHERE 1=1", []
    if termo:
        sql += " AND (nome LIKE ? OR descricao LIKE ?)"
        params += [f"%{termo}%", f"%{termo}%"]
    if categoria:
        sql += " AND categoria = ?"
        params.append(categoria)
    if preco_min:
        sql += " AND preco >= ?"
        params.append(preco_min)
    if preco_max:
        sql += " AND preco <= ?"
        params.append(preco_max)
    sql += " ORDER BY id"
    return [serializers.produto(row) for row in get_db().execute(sql, params).fetchall()]


def criar(nome, descricao, preco, estoque, categoria):
    with transacao() as conexao:
        cursor = conexao.execute(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            (nome, descricao, preco, estoque, categoria),
        )
    return cursor.lastrowid


def atualizar(produto_id, nome, descricao, preco, estoque, categoria):
    with transacao() as conexao:
        conexao.execute(
            "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
            (nome, descricao, preco, estoque, categoria, produto_id),
        )


def remover(produto_id):
    with transacao() as conexao:
        conexao.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))


def debitar_estoque(conexao, produto_id, quantidade):
    """Debita só se houver saldo. Devolve False quando o estoque não cobre a quantidade."""
    cursor = conexao.execute(
        "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
        (quantidade, produto_id, quantidade),
    )
    return cursor.rowcount == 1
