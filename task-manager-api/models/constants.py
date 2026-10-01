from enum import StrEnum


class TaskStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"


class UserRole(StrEnum):
    USER = "user"
    ADMIN = "admin"
    MANAGER = "manager"


# Tuplas, não sets: o cliente pode mandar lista ou dict, e `in` sobre set exigiria hashable.
VALID_STATUSES = tuple(TaskStatus)
FINISHED_STATUSES = (TaskStatus.DONE, TaskStatus.CANCELLED)
VALID_ROLES = tuple(UserRole)
DEFAULT_ROLE = UserRole.USER

MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200
MIN_PRIORITY = 1
MAX_PRIORITY = 5
DEFAULT_PRIORITY = 3
HIGH_PRIORITY_THRESHOLD = 2
PRIORITY_LABELS = {1: "critical", 2: "high", 3: "medium", 4: "low", 5: "minimal"}

MIN_PASSWORD_LENGTH = 4
DEFAULT_CATEGORY_COLOR = "#000000"
DUE_DATE_FORMAT = "%Y-%m-%d"
RECENT_ACTIVITY_DAYS = 7
