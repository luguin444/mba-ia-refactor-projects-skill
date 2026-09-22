"""Constantes de domínio. Fonte única dos valores que as rotas repetiam inline."""
from enum import StrEnum


class TaskStatus(StrEnum):
    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    DONE = 'done'
    CANCELLED = 'cancelled'


class UserRole(StrEnum):
    USER = 'user'
    ADMIN = 'admin'
    MANAGER = 'manager'


VALID_STATUSES = tuple(status.value for status in TaskStatus)
VALID_ROLES = tuple(role.value for role in UserRole)

# Status em que uma task deixa de poder atrasar.
FINAL_STATUSES = frozenset({TaskStatus.DONE, TaskStatus.CANCELLED})

MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200
MIN_PRIORITY = 1
MAX_PRIORITY = 5
DEFAULT_PRIORITY = 3
MIN_PASSWORD_LENGTH = 4
DEFAULT_COLOR = '#000000'

# Formato aceito em due_date. O contrato rejeita qualquer outro.
DATE_FORMAT = '%Y-%m-%d'

EMAIL_PATTERN = r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$'
