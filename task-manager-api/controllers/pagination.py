"""Leitura dos parâmetros de paginação da query string.

Ambos são opcionais e, quando ausentes, a listagem devolve todos os registros —
o mesmo comportamento de antes. Assim a paginação fica disponível sem alterar o
contrato das rotas existentes.
"""
from flask import request

LIMITE_MAXIMO = 200


def pagination_args() -> dict:
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', type=int)
    if limit is not None:
        limit = max(1, min(limit, LIMITE_MAXIMO))
    return {'limit': limit, 'offset': offset}
