from dataclasses import dataclass
from datetime import datetime, timezone

import jwt

from config import settings
from models.constants import UserRole

ALGORITHM = 'HS256'


@dataclass(frozen=True)
class Actor:
    """Quem faz a requisição, segundo o token já verificado."""

    user_id: int
    role: str

    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN


def issue(user):
    now = datetime.now(timezone.utc)
    payload = {'sub': str(user.id), 'role': user.role, 'iat': now, 'exp': now + settings.TOKEN_TTL}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def verify(token):
    """Devolve as claims; levanta jwt.PyJWTError se o token for inválido ou expirado."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])


def actor_from_claims(claims):
    return Actor(user_id=int(claims['sub']), role=claims.get('role'))
