from dataclasses import dataclass

from flask import request

from exceptions import ValidationError

MAX_PAGE_SIZE = 200


@dataclass(frozen=True)
class Page:
    limit: int
    offset: int


def page_from_request():
    """Paginação opt-in: sem `limit` nem `offset`, devolve None e a listagem vem inteira, como sempre veio."""
    if 'limit' not in request.args and 'offset' not in request.args:
        return None
    try:
        limit = int(request.args.get('limit', MAX_PAGE_SIZE))
        offset = int(request.args.get('offset', 0))
    except ValueError:
        raise ValidationError('Parâmetros de paginação inválidos')
    if not 1 <= limit <= MAX_PAGE_SIZE or offset < 0:
        raise ValidationError('Parâmetros de paginação inválidos')
    return Page(limit=limit, offset=offset)
