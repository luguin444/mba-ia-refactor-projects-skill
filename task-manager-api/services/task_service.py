import logging
from datetime import datetime

from exceptions import ForbiddenError, NotFoundError, ValidationError
from models.constants import (
    DEFAULT_PRIORITY,
    DUE_DATE_FORMAT,
    MAX_TITLE_LENGTH,
    MIN_TITLE_LENGTH,
    TaskStatus,
)
from models.task import Task
from repositories import category_repository, task_repository, unit_of_work, user_repository
from utils.helpers import calculate_percentage, utcnow

logger = logging.getLogger(__name__)

# Mensagens de data divergem entre criar e atualizar desde o original; o contrato fixa as duas.
CREATE_DATE_ERROR = 'Formato de data inválido. Use YYYY-MM-DD'
UPDATE_DATE_ERROR = 'Formato de data inválido'


def _get_or_404(task_id):
    task = task_repository.get(task_id)
    if task is None:
        raise NotFoundError('Task não encontrada')
    return task


def _validate_title_length(title):
    if len(title) < MIN_TITLE_LENGTH:
        raise ValidationError('Título muito curto')
    if len(title) > MAX_TITLE_LENGTH:
        raise ValidationError('Título muito longo')


def _validate_status(status):
    if not Task.validate_status(status):
        raise ValidationError('Status inválido')


def _validate_priority(priority):
    if not Task.validate_priority(priority):
        raise ValidationError('Prioridade deve ser entre 1 e 5')


def _ensure_user_exists(user_id):
    if user_id and user_repository.get(user_id) is None:
        raise NotFoundError('Usuário não encontrado')


def _ensure_category_exists(category_id):
    if category_id and category_repository.get(category_id) is None:
        raise NotFoundError('Categoria não encontrada')


def _parse_due_date(value, error_message):
    try:
        return datetime.strptime(value, DUE_DATE_FORMAT)
    except (ValueError, TypeError):
        raise ValidationError(error_message)


def _join_tags(tags):
    return ','.join(tags) if isinstance(tags, list) else tags


def _authorize_write(task, actor):
    """Edita ou apaga quem é responsável pela task; task sem responsável, só admin."""
    if actor.is_admin:
        return
    if task.user_id is None or task.user_id != actor.user_id:
        raise ForbiddenError('Recurso de outro usuário')


def list_board(page=None):
    return [task.to_board_dict() for task in task_repository.list_with_relations(page)]


def get_detail(task_id):
    return _get_or_404(task_id).to_detail_dict()


def create(data):
    if not data:
        raise ValidationError('Dados inválidos')

    title = data.get('title')
    if not title:
        raise ValidationError('Título é obrigatório')
    _validate_title_length(title)

    status = data.get('status', TaskStatus.PENDING.value)
    priority = data.get('priority', DEFAULT_PRIORITY)
    user_id = data.get('user_id')
    category_id = data.get('category_id')
    due_date = data.get('due_date')
    tags = data.get('tags')

    _validate_status(status)
    _validate_priority(priority)
    _ensure_user_exists(user_id)
    _ensure_category_exists(category_id)

    task = Task(
        title=title,
        description=data.get('description', ''),
        status=status,
        priority=priority,
        user_id=user_id,
        category_id=category_id,
    )
    if due_date:
        task.due_date = _parse_due_date(due_date, CREATE_DATE_ERROR)
    if tags:
        task.tags = _join_tags(tags)

    unit_of_work.add(task)
    unit_of_work.commit('Erro ao criar task')
    logger.info('Task criada: %s - %s', task.id, task.title)
    return task.to_dict()


def get_for_write(task_id, actor):
    """Busca a task (404) e confere se o ator pode alterá-la (403), antes de qualquer leitura do corpo."""
    task = _get_or_404(task_id)
    _authorize_write(task, actor)
    return task


def update(task, data):
    if not data:
        raise ValidationError('Dados inválidos')

    if 'title' in data:
        _validate_title_length(data['title'])
        task.title = data['title']

    if 'description' in data:
        task.description = data['description']

    if 'status' in data:
        _validate_status(data['status'])
        task.status = data['status']

    if 'priority' in data:
        _validate_priority(data['priority'])
        task.priority = data['priority']

    if 'user_id' in data:
        _ensure_user_exists(data['user_id'])
        task.user_id = data['user_id']

    if 'category_id' in data:
        _ensure_category_exists(data['category_id'])
        task.category_id = data['category_id']

    if 'due_date' in data:
        task.due_date = _parse_due_date(data['due_date'], UPDATE_DATE_ERROR) if data['due_date'] else None

    if 'tags' in data:
        task.tags = _join_tags(data['tags'])

    task.updated_at = utcnow()

    unit_of_work.commit('Erro ao atualizar')
    logger.info('Task atualizada: %s', task.id)
    return task.to_dict()


def delete(task_id, actor):
    task = get_for_write(task_id, actor)
    unit_of_work.delete(task)
    unit_of_work.commit('Erro ao deletar')
    logger.info('Task deletada: %s', task_id)


def search(text='', status='', priority=None, user_id=None, page=None):
    tasks = task_repository.search(text=text, status=status, priority=priority, user_id=user_id, page=page)
    return [task.to_dict() for task in tasks]


def stats():
    total = task_repository.count()
    by_status = task_repository.count_by_status()
    done = by_status.get(TaskStatus.DONE, 0)
    overdue = sum(1 for task in task_repository.list_all() if task.is_overdue())

    return {
        'total': total,
        'pending': by_status.get(TaskStatus.PENDING, 0),
        'in_progress': by_status.get(TaskStatus.IN_PROGRESS, 0),
        'done': done,
        'cancelled': by_status.get(TaskStatus.CANCELLED, 0),
        'overdue': overdue,
        'completion_rate': calculate_percentage(done, total),
    }
