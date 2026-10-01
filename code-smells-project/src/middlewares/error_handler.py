import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from src.errors import AppError

logger = logging.getLogger(__name__)

MENSAGEM_ERRO_INTERNO = "Erro interno do servidor"


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def _erro_de_dominio(erro):
        corpo = {"erro": erro.mensagem}
        if erro.com_sucesso:
            corpo["sucesso"] = False
        return jsonify(corpo), erro.status

    @app.errorhandler(HTTPException)
    def _erro_http(erro):
        # 404 de rota inexistente, 405 etc.: resposta padrão do framework, como antes.
        return erro

    @app.errorhandler(Exception)
    def _erro_inesperado(_erro):
        logger.exception("erro não tratado")
        return jsonify({"erro": MENSAGEM_ERRO_INTERNO}), 500
