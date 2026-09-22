"""Conexão com o banco, uma por requisição.

Substitui o singleton global de módulo: cada requisição abre e fecha a sua conexão,
de modo que o commit de um handler nunca confirma o trabalho parcial de outro.
"""
import sqlite3

from flask import g

from src.config.settings import settings


def abrir_conexao(caminho: str | None = None) -> sqlite3.Connection:
    """Abre uma conexão nova. Usada pela requisição e pelos comandos de schema/seed."""
    conexao = sqlite3.connect(caminho or settings.DATABASE_PATH)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def get_db() -> sqlite3.Connection:
    """Conexão da requisição corrente, criada sob demanda e guardada em `flask.g`."""
    if "db" not in g:
        g.db = abrir_conexao()
    return g.db


def fechar_conexao(_exc=None) -> None:
    """Registrado em `teardown_appcontext`: devolve a conexão ao fim da requisição."""
    conexao = g.pop("db", None)
    if conexao is not None:
        conexao.close()
