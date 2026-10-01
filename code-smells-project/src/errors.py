"""Erros de domínio. O middleware de erro traduz cada um no status HTTP correspondente.

`com_sucesso=True` acrescenta `"sucesso": false` ao corpo — as rotas que já
devolviam esse campo no erro continuam devolvendo.
"""


class AppError(Exception):
    status = 400

    def __init__(self, mensagem, *, com_sucesso=False):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.com_sucesso = com_sucesso


class ValidacaoError(AppError):
    status = 400


class NaoAutenticadoError(AppError):
    status = 401


class ProibidoError(AppError):
    status = 403


class NaoEncontradoError(AppError):
    status = 404


class ConflitoError(AppError):
    status = 409
