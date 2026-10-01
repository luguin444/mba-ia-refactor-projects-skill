"""Autenticação e autorização. A rota declara o nível; este módulo sabe verificar."""
from functools import wraps

import jwt
from flask import g, request

from src.errors import NaoAutenticadoError, ProibidoError
from src.models.constants import TipoUsuario
from src.services import token_service


def _eh_admin():
    return g.claims.get("role") == TipoUsuario.ADMIN


def requer_autenticacao(f):
    @wraps(f)
    def _wrapper(*args, **kwargs):
        cabecalho = request.headers.get("Authorization", "")
        if not cabecalho.startswith("Bearer "):
            raise NaoAutenticadoError("Credencial ausente")
        try:
            g.claims = token_service.verificar(cabecalho[len("Bearer "):])
        except jwt.PyJWTError:
            raise NaoAutenticadoError("Credencial inválida") from None
        return f(*args, **kwargs)
    return _wrapper


def requer_admin(f):
    @wraps(f)
    @requer_autenticacao
    def _wrapper(*args, **kwargs):
        if not _eh_admin():
            raise ProibidoError("Requer perfil administrativo")
        return f(*args, **kwargs)
    return _wrapper


def requer_dono_ou_admin(parametro):
    """Compara o `sub` do token com o id de sujeito no caminho. Admin passa sempre."""
    def _decorador(f):
        @wraps(f)
        @requer_autenticacao
        def _wrapper(*args, **kwargs):
            exigir_dono_ou_admin(kwargs.get(parametro))
            return f(*args, **kwargs)
        return _wrapper
    return _decorador


def exigir_dono_ou_admin(usuario_id):
    """Mesma checagem, para quando o id de sujeito vem no corpo. Exige `requer_autenticacao` antes."""
    if not _eh_admin() and str(usuario_id) != g.claims.get("sub"):
        raise ProibidoError("Recurso de outro usuário")
