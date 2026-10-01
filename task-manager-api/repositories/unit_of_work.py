import logging

from sqlalchemy.exc import SQLAlchemyError

from database import db
from exceptions import AppError

logger = logging.getLogger(__name__)


def add(entity):
    db.session.add(entity)


def delete(entity):
    db.session.delete(entity)


def commit(error_message):
    """Confirma a transação; em falha, desfaz, registra e responde 500 com a mensagem da operação."""
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("falha ao confirmar transação: %s", error_message)
        raise AppError(error_message, 500)
