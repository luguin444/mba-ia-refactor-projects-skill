import hashlib
import re

from werkzeug.security import check_password_hash, generate_password_hash

from database import db
from models.constants import UserRole
from utils.helpers import utc_now

# Hashes gravados pela versão anterior: MD5 sem salt, 32 caracteres hex.
_LEGACY_MD5 = re.compile(r'^[0-9a-f]{32}$')


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=UserRole.USER.value)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    tasks = db.relationship(
        'Task',
        back_populates='user',
        cascade='all, delete-orphan',
        passive_deletes=True,
    )

    def set_password(self, senha: str) -> None:
        self.password = generate_password_hash(senha)

    def has_legacy_password(self) -> bool:
        """Indica hash MD5 herdado, que precisa ser reescrito no próximo login."""
        return bool(_LEGACY_MD5.match(self.password or ''))

    def check_password(self, senha: str) -> bool:
        if self.has_legacy_password():
            return hashlib.md5(senha.encode()).hexdigest() == self.password
        return check_password_hash(self.password, senha)

    def to_dict(self) -> dict:
        """Serializa o usuário.

        `password` não entra: o hash era devolvido ao cliente por quatro rotas.
        """
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at),
        }
