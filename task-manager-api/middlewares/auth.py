"""Autenticação e autorização por rota. A rota declara o nível; este módulo sabe verificar."""
from functools import wraps

import jwt
from flask import g, request

from exceptions import ForbiddenError, UnauthorizedError
from services import token_service


def current_actor():
    return g.actor


def require_auth(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        header = request.headers.get('Authorization', '')
        if not header.startswith('Bearer '):
            raise UnauthorizedError('Credencial ausente')
        try:
            g.actor = token_service.actor_from_claims(token_service.verify(header[len('Bearer '):]))
        except (jwt.PyJWTError, KeyError, ValueError):
            raise UnauthorizedError('Credencial inválida')
        return view(*args, **kwargs)
    return wrapper


def require_admin(view):
    @wraps(view)
    @require_auth
    def wrapper(*args, **kwargs):
        if not g.actor.is_admin:
            raise ForbiddenError('Requer perfil administrativo')
        return view(*args, **kwargs)
    return wrapper


def require_owner_or_admin(param):
    """Compara o usuário do token com o id de usuário no caminho; admin passa sempre."""
    def decorator(view):
        @wraps(view)
        @require_auth
        def wrapper(*args, **kwargs):
            if not g.actor.is_admin and kwargs.get(param) != g.actor.user_id:
                raise ForbiddenError('Recurso de outro usuário')
            return view(*args, **kwargs)
        return wrapper
    return decorator
