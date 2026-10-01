import re
from datetime import datetime, timezone

EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$")


def utcnow() -> datetime:
    """UTC atual, sem tzinfo: o banco guarda datetimes naive e o `str()` delas é contrato."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def calculate_percentage(part, total):
    if total == 0:
        return 0
    return round((part / total) * 100, 2)


def validate_email(email):
    return bool(EMAIL_PATTERN.match(email))
