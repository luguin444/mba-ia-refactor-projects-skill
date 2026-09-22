"""Regra de negócio de User: validação, credenciais e ciclo de vida."""
import logging

from exceptions import (
    AppError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
)
from models.constants import MIN_PASSWORD_LENGTH, VALID_ROLES, UserRole
from models.user import User
from repositories import unit_of_work, user_repository
from utils.helpers import is_valid_email

logger = logging.getLogger(__name__)


def _validate_email(email: str) -> str:
    if not is_valid_email(email):
        raise AppError('Email inválido')
    return email


def _validate_role(role: str) -> str:
    if role not in VALID_ROLES:
        raise AppError('Role inválido')
    return role


def _assert_email_disponivel(email: str, ignorar_id: int | None = None) -> None:
    existente = user_repository.get_by_email(email)
    if existente and existente.id != ignorar_id:
        raise ConflictError('Email já cadastrado')


def list_users(*, limit=None, offset=None) -> list[User]:
    return user_repository.list_all(limit=limit, offset=offset)


def get_user(user_id: int) -> User:
    user = user_repository.get_by_id(user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')
    return user


def create_user(data: dict) -> User:
    if not data:
        raise AppError('Dados inválidos')

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not name:
        raise AppError('Nome é obrigatório')
    if not email:
        raise AppError('Email é obrigatório')
    if not password:
        raise AppError('Senha é obrigatória')

    _validate_email(email)
    if len(password) < MIN_PASSWORD_LENGTH:
        raise AppError('Senha deve ter no mínimo 4 caracteres')
    _assert_email_disponivel(email)
    role = _validate_role(data.get('role', UserRole.USER.value))

    user = User()
    user.name = name
    user.email = email
    user.set_password(password)
    user.role = role

    user_repository.add(user)
    unit_of_work.commit()
    logger.info('usuário criado', extra={'user_id': user.id})
    return user


def update_user(user_id: int, data: dict) -> User:
    user = get_user(user_id)
    if not data:
        raise AppError('Dados inválidos')

    if 'name' in data:
        user.name = data['name']
    if 'email' in data:
        _validate_email(data['email'])
        _assert_email_disponivel(data['email'], ignorar_id=user_id)
        user.email = data['email']
    if 'password' in data:
        if len(data['password']) < MIN_PASSWORD_LENGTH:
            raise AppError('Senha muito curta')
        user.set_password(data['password'])
    if 'role' in data:
        user.role = _validate_role(data['role'])
    if 'active' in data:
        user.active = data['active']

    unit_of_work.commit()
    logger.info('usuário atualizado', extra={'user_id': user.id})
    return user


def delete_user(user_id: int) -> None:
    """Remove o usuário. As tasks dele caem junto pelo cascade do relacionamento."""
    user = get_user(user_id)
    user_repository.remove(user)
    unit_of_work.commit()
    logger.info('usuário removido', extra={'user_id': user_id})


def authenticate(data: dict) -> User:
    if not data:
        raise AppError('Dados inválidos')

    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        raise AppError('Email e senha são obrigatórios')

    user = user_repository.get_by_email(email)
    if not user or not user.check_password(password):
        raise UnauthorizedError('Credenciais inválidas')
    if not user.active:
        raise ForbiddenError('Usuário inativo')

    if user.has_legacy_password():
        # Migração dos hashes MD5 herdados: reescreve com scrypt agora que a
        # senha em claro está disponível e confirmada.
        user.set_password(password)
        unit_of_work.commit()
        logger.info('hash de senha migrado para scrypt', extra={'user_id': user.id})

    return user


# Prefixo do token emitido pelo login. NÃO é credencial: a string é previsível,
# não é assinada e nenhuma rota a verifica. Preservado porque faz parte do
# contrato atual; substituí-lo por JWT real é decisão de produto (AP-07).
STUB_TOKEN_PREFIX = 'fake-jwt-token-'


def issue_token(user: User) -> str:
    logger.warning(
        'emitindo token stub, previsível e não verificado; '
        'autenticação real ainda não foi implementada',
        extra={'user_id': user.id},
    )
    return f'{STUB_TOKEN_PREFIX}{user.id}'
