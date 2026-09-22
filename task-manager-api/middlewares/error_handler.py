"""Tratamento central de erro. Substitui os doze `except:` nus das rotas."""
import logging

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from database import db
from exceptions import AppError

logger = logging.getLogger(__name__)


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(AppError)
    def _app_error(exc: AppError):
        return jsonify({'error': exc.mensagem}), exc.status

    @app.errorhandler(HTTPException)
    def _http_error(exc: HTTPException):
        return jsonify({'error': exc.description}), exc.code

    @app.errorhandler(Exception)
    def _unexpected(exc: Exception):
        # A sessão pode ter ficado suja; desfaz antes de devolver a resposta.
        db.session.rollback()
        logger.exception('erro não tratado')
        return jsonify({'error': 'Erro interno'}), 500
