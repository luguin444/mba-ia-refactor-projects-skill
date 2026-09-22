"""Tratamento de erro centralizado. Substitui os 17 `try/except` idênticos dos handlers."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Erro de domínio traduzido em resposta HTTP.

    `incluir_sucesso` existe porque o contrato original não é uniforme: parte das rotas
    devolve `{"erro": ...}` e parte devolve `{"erro": ..., "sucesso": false}`.
    """

    def __init__(self, mensagem: str, status: int = 400, incluir_sucesso: bool = False):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status = status
        self.incluir_sucesso = incluir_sucesso

    def to_response(self):
        corpo = {"erro": self.mensagem}
        if self.incluir_sucesso:
            corpo["sucesso"] = False
        return jsonify(corpo), self.status


def registrar_error_handlers(app) -> None:
    @app.errorhandler(AppError)
    def _erro_de_dominio(erro: AppError):
        return erro.to_response()

    @app.errorhandler(HTTPException)
    def _erro_http(erro: HTTPException):
        # 404 de rota inexistente e 405 de método errado continuam sendo 404 e 405 —
        # o catch-all abaixo os transformaria em 500.
        return erro

    @app.errorhandler(Exception)
    def _erro_inesperado(erro: Exception):
        # A mensagem crua da exceção não vai para o cliente: ela vazava nome de tabela e SQL.
        logger.exception("erro não tratado")
        return jsonify({"erro": "Erro interno", "sucesso": False}), 500
