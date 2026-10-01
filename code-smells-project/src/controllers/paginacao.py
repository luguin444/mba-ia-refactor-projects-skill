from flask import request

from src.errors import ValidacaoError
from src.models.constants import LIMITE_MAXIMO_PAGINA


def ler_paginacao():
    """`limit`/`offset` opcionais. Sem `limit`, a listagem vem inteira (contrato original)."""
    limite, offset = request.args.get("limit"), request.args.get("offset", "0")
    try:
        offset = int(offset)
        limite = None if limite is None else min(int(limite), LIMITE_MAXIMO_PAGINA)
    except ValueError:
        raise ValidacaoError("limit e offset devem ser inteiros") from None
    if offset < 0 or (limite is not None and limite < 1):
        raise ValidacaoError("limit deve ser positivo e offset não negativo")
    return limite, offset
