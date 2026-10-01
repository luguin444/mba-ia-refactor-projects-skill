from src.database.connection import get_db, transacao
from src.database.paginacao import aplicar_limite
from src.models import serializers

# Uma query por listagem: a paginação se aplica aos pedidos (subquery), e itens e
# nome do produto vêm por JOIN. LEFT JOIN em produtos preserva itens de produto apagado.
_LISTAGEM = """
    SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
           i.id AS item_id, i.produto_id, i.quantidade, i.preco_unitario,
           pr.id AS produto_existe, pr.nome AS produto_nome
    FROM ({pedidos}) p
    LEFT JOIN itens_pedido i ON i.pedido_id = p.id
    LEFT JOIN produtos pr    ON pr.id = i.produto_id
    ORDER BY p.id, i.id
"""


def _listar(filtro, params, limite, offset):
    pedidos, params = aplicar_limite("SELECT * FROM pedidos" + filtro + " ORDER BY id", params, limite, offset)
    rows = get_db().execute(_LISTAGEM.format(pedidos=pedidos), params).fetchall()

    resultado, por_id = [], {}
    for row in rows:
        pedido = por_id.get(row["id"])
        if pedido is None:
            pedido = por_id[row["id"]] = serializers.pedido(row)
            resultado.append(pedido)
        if row["item_id"] is not None:
            pedido["itens"].append(serializers.item_pedido(row))
    return resultado


def listar(limite=None, offset=0):
    return _listar("", [], limite, offset)


def listar_por_usuario(usuario_id, limite=None, offset=0):
    return _listar(" WHERE usuario_id = ?", [usuario_id], limite, offset)


def inserir(conexao, usuario_id, total):
    cursor = conexao.execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
        (usuario_id, total),
    )
    return cursor.lastrowid


def inserir_item(conexao, pedido_id, produto_id, quantidade, preco_unitario):
    conexao.execute(
        "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
        (pedido_id, produto_id, quantidade, preco_unitario),
    )


def atualizar_status(pedido_id, status):
    with transacao() as conexao:
        conexao.execute("UPDATE pedidos SET status = ? WHERE id = ?", (status, pedido_id))
