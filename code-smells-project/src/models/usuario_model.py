"""Acesso a dados de usuário. A verificação de senha é feita na aplicação, nunca no WHERE."""
from src.database.connection import get_db
from src.models.serializers import serializar_usuario


def listar(limite: int | None = None, deslocamento: int | None = None) -> list[dict]:
    query, params = "SELECT * FROM usuarios ORDER BY id", []
    if limite is not None:
        query += " LIMIT ?"
        params.append(limite)
        if deslocamento:
            query += " OFFSET ?"
            params.append(deslocamento)
    return [serializar_usuario(linha) for linha in get_db().execute(query, params).fetchall()]


def buscar_por_id(usuario_id: int) -> dict | None:
    linha = get_db().execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    return serializar_usuario(linha) if linha else None


def buscar_linha_por_email(email: str):
    """Devolve a linha crua, com o hash — só o serviço de autenticação usa."""
    return get_db().execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()


def criar(nome: str, email: str, senha_hash: str, tipo: str = "cliente") -> int:
    conexao = get_db()
    cursor = conexao.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, senha_hash, tipo),
    )
    conexao.commit()
    return cursor.lastrowid


def contar() -> int:
    return get_db().execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
