"""Regra de negócio de Task: validação de domínio, criação, atualização e métricas."""
import logging
from datetime import datetime

from exceptions import AppError, NotFoundError
from models.constants import (
    DATE_FORMAT,
    DEFAULT_PRIORITY,
    MAX_PRIORITY,
    MAX_TITLE_LENGTH,
    MIN_PRIORITY,
    MIN_TITLE_LENGTH,
    VALID_STATUSES,
    TaskStatus,
)
from models.task import Task
from repositories import category_repository, task_repository, unit_of_work, user_repository
from utils.helpers import calculate_percentage

logger = logging.getLogger(__name__)


def _validate_title(title) -> str:
    if not title:
        raise AppError('Título é obrigatório')
    if len(title) < MIN_TITLE_LENGTH:
        raise AppError('Título muito curto')
    if len(title) > MAX_TITLE_LENGTH:
        raise AppError('Título muito longo')
    return title


def _validate_status(status: str) -> str:
    if status not in VALID_STATUSES:
        raise AppError('Status inválido')
    return status


def _validate_priority(priority: int) -> int:
    if priority < MIN_PRIORITY or priority > MAX_PRIORITY:
        raise AppError('Prioridade deve ser entre 1 e 5')
    return priority


def _parse_due_date(valor: str, mensagem_erro: str) -> datetime:
    try:
        return datetime.strptime(valor, DATE_FORMAT)
    except (ValueError, TypeError):
        raise AppError(mensagem_erro)


def _serialize_tags(tags) -> str:
    return ','.join(tags) if isinstance(tags, list) else tags


def _assert_user_exists(user_id) -> None:
    if user_id and not user_repository.get_by_id(user_id):
        raise NotFoundError('Usuário não encontrado')


def _assert_category_exists(category_id) -> None:
    if category_id and not category_repository.get_by_id(category_id):
        raise NotFoundError('Categoria não encontrada')


def list_tasks(*, limit=None, offset=None) -> list[Task]:
    return task_repository.list_all(with_relations=True, limit=limit, offset=offset)


def get_task(task_id: int) -> Task:
    task = task_repository.get_by_id(task_id)
    if not task:
        raise NotFoundError('Task não encontrada')
    return task


def search_tasks(*, termo='', status='', priority=None, user_id=None, limit=None, offset=None) -> list[Task]:
    return task_repository.search(
        termo=termo, status=status, priority=priority,
        user_id=user_id, limit=limit, offset=offset,
    )


def list_tasks_of_user(user_id: int) -> list[Task]:
    return task_repository.list_by_user(user_id)


def create_task(data: dict) -> Task:
    if not data:
        raise AppError('Dados inválidos')

    task = Task()
    task.title = _validate_title(data.get('title'))
    task.description = data.get('description', '')
    task.status = _validate_status(data.get('status', TaskStatus.PENDING.value))
    task.priority = _validate_priority(data.get('priority', DEFAULT_PRIORITY))

    user_id = data.get('user_id')
    category_id = data.get('category_id')
    _assert_user_exists(user_id)
    _assert_category_exists(category_id)
    task.user_id = user_id
    task.category_id = category_id

    due_date = data.get('due_date')
    if due_date:
        task.due_date = _parse_due_date(due_date, 'Formato de data inválido. Use YYYY-MM-DD')

    tags = data.get('tags')
    if tags:
        task.tags = _serialize_tags(tags)

    task_repository.add(task)
    unit_of_work.commit()
    logger.info('task criada', extra={'task_id': task.id})
    return task


def update_task(task_id: int, data: dict) -> Task:
    task = get_task(task_id)
    if not data:
        raise AppError('Dados inválidos')

    if 'title' in data:
        task.title = _validate_title(data['title'])
    if 'description' in data:
        task.description = data['description']
    if 'status' in data:
        task.status = _validate_status(data['status'])
    if 'priority' in data:
        task.priority = _validate_priority(data['priority'])
    if 'user_id' in data:
        _assert_user_exists(data['user_id'])
        task.user_id = data['user_id']
    if 'category_id' in data:
        _assert_category_exists(data['category_id'])
        task.category_id = data['category_id']
    if 'due_date' in data:
        task.due_date = (
            _parse_due_date(data['due_date'], 'Formato de data inválido')
            if data['due_date'] else None
        )
    if 'tags' in data:
        task.tags = _serialize_tags(data['tags'])

    unit_of_work.commit()
    logger.info('task atualizada', extra={'task_id': task.id})
    return task


def delete_task(task_id: int) -> None:
    task = get_task(task_id)
    task_repository.remove(task)
    unit_of_work.commit()
    logger.info('task removida', extra={'task_id': task_id})


def count_overdue() -> int:
    return sum(1 for task in task_repository.list_overdue_candidates() if task.is_overdue())


def build_stats() -> dict:
    total = task_repository.count_all()
    por_status = task_repository.count_by_status()
    done = por_status.get(TaskStatus.DONE.value, 0)
    return {
        'total': total,
        'pending': por_status.get(TaskStatus.PENDING.value, 0),
        'in_progress': por_status.get(TaskStatus.IN_PROGRESS.value, 0),
        'done': done,
        'cancelled': por_status.get(TaskStatus.CANCELLED.value, 0),
        'overdue': count_overdue(),
        'completion_rate': calculate_percentage(done, total),
    }
