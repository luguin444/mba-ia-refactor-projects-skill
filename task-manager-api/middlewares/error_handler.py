import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from exceptions import AppError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(error):
        return jsonify({'error': error.message}), error.status

    @app.errorhandler(Exception)
    def handle_unexpected(error):
        # Erros HTTP do próprio Flask (415, 400 de JSON malformado, 404, 405) seguem com a resposta padrão.
        if isinstance(error, HTTPException):
            return error
        logger.exception('erro não tratado')
        return jsonify({'error': 'Erro interno'}), 500
