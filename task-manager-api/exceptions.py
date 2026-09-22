"""Erros de domínio.

Vivem fora de `middlewares/` de propósito: os serviços os levantam e não devem
depender da camada HTTP para isso. Quem traduz cada um em resposta é o handler
central em `middlewares/error_handler.py`.
"""


class AppError(Exception):
    """Erro de domínio com status HTTP. O corpo emitido é `{'error': <mensagem>}`."""

    status = 400

    def __init__(self, mensagem: str, status: int | None = None):
        super().__init__(mensagem)
        self.mensagem = mensagem
        if status is not None:
            self.status = status


class UnauthorizedError(AppError):
    status = 401


class ForbiddenError(AppError):
    status = 403


class NotFoundError(AppError):
    status = 404


class ConflictError(AppError):
    status = 409
