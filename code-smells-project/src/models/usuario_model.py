import sqlite3

from src.database.connection import get_db, transacao
from src.database.paginacao import aplicar_limite
from src.errors import ConflitoError
from src.models import serializers


def listar(limite=None, offset=0):
    sql, params = aplicar_limite("SELECT * FROM usuarios ORDER BY id", [], limite, offset)
    return [serializers.usuario(row) for row in get_db().execute(sql, params).fetchall()]


def buscar_por_id(usuario_id):
    row = get_db().execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    return serializers.usuario(row) if row else None


def existe(usuario_id):
    return get_db().execute("SELECT 1 FROM usuarios WHERE id = ?", (usuario_id,)).fetchone() is not None


def buscar_credenciais_por_email(email):
    """Linha completa, com o hash da senha. Uso exclusivo da autenticação."""
    return get_db().execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()


def criar(nome, email, senha_hash, tipo):
    try:
        with transacao() as conexao:
            cursor = conexao.execute(
                "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                (nome, email, senha_hash, tipo),
            )
    except sqlite3.IntegrityError as erro:
        if "UNIQUE" in str(erro):
            raise ConflitoError("Email já cadastrado") from erro
        raise
    return cursor.lastrowid
