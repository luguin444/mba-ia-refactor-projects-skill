from datetime import timedelta

from exceptions import NotFoundError
from models.constants import HIGH_PRIORITY_THRESHOLD, PRIORITY_LABELS, RECENT_ACTIVITY_DAYS, TaskStatus
from repositories import category_repository, task_repository, user_repository
from utils.helpers import calculate_percentage, utcnow


def _user_productivity(user):
    total = len(user.tasks)
    completed = sum(1 for task in user.tasks if task.status == TaskStatus.DONE)
    return {
        'user_id': user.id,
        'user_name': user.name,
        'total_tasks': total,
        'completed_tasks': completed,
        'completion_rate': calculate_percentage(completed, total),
    }


def summary():
    by_status = task_repository.count_by_status()
    by_priority = task_repository.count_by_priority()
    overdue_tasks = [task for task in task_repository.list_all() if task.is_overdue()]
    recent_since = utcnow() - timedelta(days=RECENT_ACTIVITY_DAYS)

    return {
        'generated_at': str(utcnow()),
        'overview': {
            'total_tasks': task_repository.count(),
            'total_users': user_repository.count(),
            'total_categories': category_repository.count(),
        },
        'tasks_by_status': {status.value: by_status.get(status, 0) for status in TaskStatus},
        'tasks_by_priority': {label: by_priority.get(priority, 0) for priority, label in PRIORITY_LABELS.items()},
        'overdue': {
            'count': len(overdue_tasks),
            'tasks': [task.to_overdue_dict() for task in overdue_tasks],
        },
        'recent_activity': {
            'tasks_created_last_7_days': task_repository.count_created_since(recent_since),
            'tasks_completed_last_7_days': task_repository.count_with_status_updated_since(
                TaskStatus.DONE, recent_since
            ),
        },
        'user_productivity': [_user_productivity(user) for user in user_repository.list_with_tasks()],
    }


def user_report(user_id):
    user = user_repository.get(user_id)
    if user is None:
        raise NotFoundError('Usuário não encontrado')

    tasks = task_repository.list_by_user(user_id)
    by_status = {status: 0 for status in TaskStatus}
    for task in tasks:
        if task.status in by_status:
            by_status[task.status] += 1
    done = by_status[TaskStatus.DONE]

    return {
        'user': user.to_brief_dict(),
        'statistics': {
            'total_tasks': len(tasks),
            'done': done,
            'pending': by_status[TaskStatus.PENDING],
            'in_progress': by_status[TaskStatus.IN_PROGRESS],
            'cancelled': by_status[TaskStatus.CANCELLED],
            'overdue': sum(1 for task in tasks if task.is_overdue()),
            'high_priority': sum(1 for task in tasks if task.priority <= HIGH_PRIORITY_THRESHOLD),
            'completion_rate': calculate_percentage(done, len(tasks)),
        },
    }
