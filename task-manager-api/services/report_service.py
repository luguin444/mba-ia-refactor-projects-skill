"""Relatórios: regra de negócio que atravessa Task, User e Category."""
from datetime import timedelta

from models.constants import TaskStatus
from models.user import User
from repositories import category_repository, task_repository, user_repository
from services import task_service
from utils.helpers import calculate_percentage, utc_now

JANELA_ATIVIDADE_RECENTE = timedelta(days=7)

# Rótulo de negócio para cada nível de prioridade, na ordem em que o relatório expõe.
ROTULOS_PRIORIDADE = {1: 'critical', 2: 'high', 3: 'medium', 4: 'low', 5: 'minimal'}

PRIORIDADE_ALTA_MAXIMA = 2


def _overdue_details() -> tuple[int, list[dict]]:
    agora = utc_now()
    atrasadas = [t for t in task_repository.list_overdue_candidates() if t.is_overdue()]
    detalhes = [
        {
            'id': task.id,
            'title': task.title,
            'due_date': str(task.due_date),
            'days_overdue': (agora - task.due_date).days,
        }
        for task in atrasadas
    ]
    return len(atrasadas), detalhes


def _user_productivity() -> list[dict]:
    produtividade = task_repository.productivity_by_user()
    linhas = []
    for user in user_repository.list_all():
        total, concluidas = produtividade.get(user.id, (0, 0))
        linhas.append({
            'user_id': user.id,
            'user_name': user.name,
            'total_tasks': total,
            'completed_tasks': concluidas,
            'completion_rate': calculate_percentage(concluidas, total),
        })
    return linhas


def build_summary() -> dict:
    por_status = task_repository.count_by_status()
    por_prioridade = task_repository.count_by_priority()
    overdue_count, overdue_list = _overdue_details()
    desde = utc_now() - JANELA_ATIVIDADE_RECENTE

    return {
        'generated_at': str(utc_now()),
        'overview': {
            'total_tasks': task_repository.count_all(),
            'total_users': user_repository.count_all(),
            'total_categories': category_repository.count_all(),
        },
        'tasks_by_status': {
            status.value: por_status.get(status.value, 0) for status in TaskStatus
        },
        'tasks_by_priority': {
            rotulo: por_prioridade.get(nivel, 0)
            for nivel, rotulo in ROTULOS_PRIORIDADE.items()
        },
        'overdue': {
            'count': overdue_count,
            'tasks': overdue_list,
        },
        'recent_activity': {
            'tasks_created_last_7_days': task_repository.count_created_since(desde),
            'tasks_completed_last_7_days': task_repository.count_done_since(desde),
        },
        'user_productivity': _user_productivity(),
    }


def build_user_report(user: User) -> dict:
    tasks = task_service.list_tasks_of_user(user.id)

    por_status = {status.value: 0 for status in TaskStatus}
    overdue = 0
    high_priority = 0
    for task in tasks:
        if task.status in por_status:
            por_status[task.status] += 1
        if task.priority <= PRIORIDADE_ALTA_MAXIMA:
            high_priority += 1
        if task.is_overdue():
            overdue += 1

    total = len(tasks)
    done = por_status[TaskStatus.DONE.value]

    return {
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
        },
        'statistics': {
            'total_tasks': total,
            'done': done,
            'pending': por_status[TaskStatus.PENDING.value],
            'in_progress': por_status[TaskStatus.IN_PROGRESS.value],
            'cancelled': por_status[TaskStatus.CANCELLED.value],
            'overdue': overdue,
            'high_priority': high_priority,
            'completion_rate': calculate_percentage(done, total),
        },
    }
