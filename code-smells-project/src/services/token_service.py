from datetime import datetime, timedelta, timezone

import jwt

from src.config.settings import settings

ALGORITMO = "HS256"


def emitir(usuario):
    agora = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": str(usuario["id"]),
            "role": usuario["tipo"],
            "iat": agora,
            "exp": agora + timedelta(hours=settings.TOKEN_TTL_HORAS),
        },
        settings.SECRET_KEY,
        algorithm=ALGORITMO,
    )


def verificar(token):
    """Devolve as claims ou levanta `jwt.PyJWTError`."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITMO])
