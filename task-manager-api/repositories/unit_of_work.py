"""Fronteira de transação.

A sessão do SQLAlchemy já é transacional: tudo que os repositórios registram
entra na mesma transação e é confirmado ou desfeito em bloco. O rollback do
caminho de erro fica no handler central (`middlewares/error_handler.py`), então
os serviços só precisam marcar onde a transação termina.
"""
from database import db


def commit() -> None:
    db.session.commit()


def rollback() -> None:
    db.session.rollback()
