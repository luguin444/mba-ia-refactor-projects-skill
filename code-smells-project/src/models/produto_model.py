"""Acesso a dados de produto. Só lê e grava — nenhuma regra de negócio, nenhum HTTP."""
from src.database.connection import get_db
from src.models.serializers import serializar_produto


def _paginar(query: str, params: list, limite: int | None, deslocamento: int | None) -> tuple[str, list]:
    """Anexa LIMIT/OFFSET só quando o cliente pediu — sem `limit`, a listagem é integral."""
    if limite is not None:
        query += " LIMIT ?"
        params.append(limite)
        if deslocamento:
            query += " OFFSET ?"
            params.append(deslocamento)
    return query, params


def listar(limite: int | None = None, deslocamento: int | None = None) -> list[dict]:
    query, params = _paginar("SELECT * FROM produtos ORDER BY id", [], limite, deslocamento)
    return [serializar_produto(linha) for linha in get_db().execute(query, params).fetchall()]


def buscar_por_id(produto_id: int) -> dict | None:
    linha = get_db().execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
    return serializar_produto(linha) if linha else None


def criar(nome: str, descricao: str, preco: float, estoque: int, categoria: str) -> int:
    conexao = get_db()
    cursor = conexao.execute(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        (nome, descricao, preco, estoque, categoria),
    )
    conexao.commit()
    return cursor.lastrowid


def atualizar(produto_id: int, nome: str, descricao: str, preco: float, estoque: int, categoria: str) -> None:
    conexao = get_db()
    conexao.execute(
        "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
        (nome, descricao, preco, estoque, categoria, produto_id),
    )
    conexao.commit()


def deletar(produto_id: int) -> None:
    conexao = get_db()
    conexao.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
    conexao.commit()


def buscar(
    termo: str = "",
    categoria: str | None = None,
    preco_min: float | None = None,
    preco_max: float | None = None,
    limite: int | None = None,
    deslocamento: int | None = None,
) -> list[dict]:
    query = "SELECT * FROM produtos WHERE 1=1"
    params: list = []

    if termo:
        query += " AND (nome LIKE ? OR descricao LIKE ?)"
        params.extend([f"%{termo}%", f"%{termo}%"])
    if categoria:
        query += " AND categoria = ?"
        params.append(categoria)
    if preco_min:
        query += " AND preco >= ?"
        params.append(preco_min)
    if preco_max:
        query += " AND preco <= ?"
        params.append(preco_max)

    query += " ORDER BY id"
    query, params = _paginar(query, params, limite, deslocamento)
    return [serializar_produto(linha) for linha in get_db().execute(query, params).fetchall()]


def contar() -> int:
    return get_db().execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
