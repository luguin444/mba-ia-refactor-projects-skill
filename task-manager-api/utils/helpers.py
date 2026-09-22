"""Helpers compartilhados. Só o que tem chamador."""
import re
from datetime import datetime, timezone

from models.constants import EMAIL_PATTERN

_EMAIL_REGEX = re.compile(EMAIL_PATTERN)


def utc_now() -> datetime:
    """Instante atual em UTC, sem tzinfo.

    Substitui `datetime.utcnow()`, deprecated no Python 3.12+. O tzinfo é
    descartado de propósito: as colunas DateTime do schema guardam UTC naive, e
    devolver um datetime aware mudaria `str(due_date)` de
    '2026-09-19 02:37:24.661581' para '2026-09-19 02:37:24.661581+00:00',
    alterando o corpo de toda rota que serializa uma task.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


def format_date(date_obj: datetime | None) -> str | None:
    """Serializa um datetime para o formato que o contrato expõe."""
    if date_obj:
        return str(date_obj)
    return None


def calculate_percentage(part: int, total: int) -> float:
    """Percentual de `part` sobre `total`, com duas casas. Zero quando não há total."""
    if total == 0:
        return 0
    return round((part / total) * 100, 2)


def is_valid_email(email: str) -> bool:
    return bool(_EMAIL_REGEX.match(email))
