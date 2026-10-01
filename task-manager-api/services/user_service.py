import logging

from exceptions import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError, ValidationError
from models.constants import DEFAULT_ROLE, MIN_PASSWORD_LENGTH, VALID_ROLES
from models.user import User
from repositories import task_repository, unit_of_work, user_repository
from services import token_service
from utils.helpers import validate_email

logger = logging.getLogger(__name__)


def get_or_404(user_id):
    user = user_repository.get(user_id)
    if user is None:
        raise NotFoundError('Usuário não encontrado')
    return user


def _ensure_email_available(email, owner_id=None):
    existing = user_repository.get_by_email(email)
    if existing and existing.id != owner_id:
        raise ConflictError('Email já cadastrado')


def list_with_task_count(page=None):
    task_counts = task_repository.count_by_user()
    return [
        {**user.to_dict(), 'task_count': task_counts.get(user.id, 0)}
        for user in user_repository.list_all(page)
    ]


def get_with_tasks(user_id):
    user = get_or_404(user_id)
    return {**user.to_dict(), 'tasks': [task.to_dict() for task in task_repository.list_by_user(user_id)]}


def list_tasks(user_id):
    get_or_404(user_id)
    return [task.to_owner_list_dict() for task in task_repository.list_by_user(user_id)]


def create(data):
    """Cadastro público. O papel nunca vem do cliente: todo cadastro nasce com o papel default."""
    if not data:
        raise ValidationError('Dados inválidos')

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not name:
        raise ValidationError('Nome é obrigatório')
    if not email:
        raise ValidationError('Email é obrigatório')
    if not password:
        raise ValidationError('Senha é obrigatória')
    if not validate_email(email):
        raise ValidationError('Email inválido')
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError('Senha deve ter no mínimo 4 caracteres')
    _ensure_email_available(email)

    user = User(name=name, email=email, role=DEFAULT_ROLE.value)
    user.set_password(password)

    unit_of_work.add(user)
    unit_of_work.commit('Erro ao criar usuário')
    logger.info('Usuário criado: %s - %s', user.id, user.name)
    return user.to_dict()


def update(user, data, actor):
    """`role` e `active` conferem acesso: só admin os altera; para os demais são ignorados."""
    if not data:
        raise ValidationError('Dados inválidos')

    if 'name' in data:
        user.name = data['name']

    if 'email' in data:
        if not validate_email(data['email']):
            raise ValidationError('Email inválido')
        _ensure_email_available(data['email'], owner_id=user.id)
        user.email = data['email']

    # A mensagem difere da do cadastro desde o original; o contrato fixa as duas.
    if 'password' in data:
        if len(data['password']) < MIN_PASSWORD_LENGTH:
            raise ValidationError('Senha muito curta')
        user.set_password(data['password'])

    if actor.is_admin:
        if 'role' in data:
            if data['role'] not in VALID_ROLES:
                raise ValidationError('Role inválido')
            user.role = data['role']
        if 'active' in data:
            user.active = data['active']

    unit_of_work.commit('Erro ao atualizar')
    return user.to_dict()


def delete(user_id):
    user = get_or_404(user_id)
    unit_of_work.delete(user)  # cascade do relacionamento apaga as tasks na mesma transação
    unit_of_work.commit('Erro ao deletar')
    logger.info('Usuário deletado: %s', user_id)


def authenticate(data):
    if not data:
        raise ValidationError('Dados inválidos')

    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        raise ValidationError('Email e senha são obrigatórios')

    user = user_repository.get_by_email(email)
    if user is None or not user.check_password(password):
        raise UnauthorizedError('Credenciais inválidas')
    if not user.active:
        raise ForbiddenError('Usuário inativo')

    return user.to_dict(), token_service.issue(user)
