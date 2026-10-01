import sqlite3
from contextlib import contextmanager

from flask import g

from src.config.settings import settings


def get_db():
    """Conexão da requisição corrente, aberta sob demanda e fechada no teardown."""
    if "db" not in g:
        conexao = sqlite3.connect(settings.DATABASE_PATH)
        conexao.row_factory = sqlite3.Row
        conexao.execute("PRAGMA foreign_keys = ON")
        g.db = conexao
    return g.db


def close_db(_erro=None):
    conexao = g.pop("db", None)
    if conexao is not None:
        conexao.close()


@contextmanager
def transacao():
    """Commit ao sair do bloco; rollback em qualquer exceção."""
    conexao = get_db()
    try:
        yield conexao
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise


def init_app(app):
    app.teardown_appcontext(close_db)
