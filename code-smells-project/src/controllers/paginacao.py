"""Leitura dos parâmetros opcionais de paginação.

Sem `limit` na query string a listagem continua integral — é o comportamento que o
baseline capturou, e mudar o default seria mudança de contrato.
"""
from flask import request

from src.middlewares.error_handler import AppError
from src.models.constants import LIMITE_PAGINACAO_MAXIMO


def ler_paginacao() -> tuple[int | None, int | None]:
    limite_bruto = request.args.get("limit")
    if limite_bruto is None:
        return None, None

    try:
        limite = min(int(limite_bruto), LIMITE_PAGINACAO_MAXIMO)
        deslocamento = int(request.args.get("offset", 0))
    except ValueError:
        raise AppError("Parâmetros de paginação inválidos")

    return max(limite, 0), max(deslocamento, 0)
