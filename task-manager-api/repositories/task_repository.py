"""Acesso a dados de Task. Único lugar que monta query sobre a tabela."""
from datetime import datetime

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import joinedload

from database import db
from models.constants import FINAL_STATUSES
from models.task import Task


def _paginate(stmt, limit: int | None, offset: int | None):
    """Aplica limit/offset quando informados.

    Sem os parâmetros a consulta devolve tudo, como antes — a paginação é
    opcional para não alterar o contrato das listagens existentes.
    """
    if offset:
        stmt = stmt.offset(offset)
    if limit is not None:
        stmt = stmt.limit(limit)
    return stmt


def list_all(*, with_relations: bool = False, limit: int | None = None, offset: int | None = None) -> list[Task]:
    stmt = select(Task).order_by(Task.id)
    if with_relations:
        stmt = stmt.options(joinedload(Task.user), joinedload(Task.category))
    stmt = _paginate(stmt, limit, offset)
    return list(db.session.execute(stmt).unique().scalars().all())


def get_by_id(task_id: int) -> Task | None:
    return db.session.get(Task, task_id)


def search(
    *,
    termo: str = '',
    status: str = '',
    priority: int | None = None,
    user_id: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> list[Task]:
    stmt = select(Task)
    if termo:
        stmt = stmt.where(
            or_(Task.title.like(f'%{termo}%'), Task.description.like(f'%{termo}%'))
        )
    if status:
        stmt = stmt.where(Task.status == status)
    if priority is not None:
        stmt = stmt.where(Task.priority == priority)
    if user_id is not None:
        stmt = stmt.where(Task.user_id == user_id)
    stmt = _paginate(stmt.order_by(Task.id), limit, offset)
    return list(db.session.execute(stmt).scalars().all())


def list_by_user(user_id: int) -> list[Task]:
    stmt = select(Task).where(Task.user_id == user_id).order_by(Task.id)
    return list(db.session.execute(stmt).scalars().all())


def count_all() -> int:
    return db.session.execute(select(func.count()).select_from(Task)).scalar_one()


def count_by_status() -> dict[str, int]:
    """Uma consulta agregada no lugar de uma contagem por status."""
    rows = db.session.execute(
        select(Task.status, func.count()).group_by(Task.status)
    ).all()
    return {status: total for status, total in rows}


def count_by_priority() -> dict[int, int]:
    rows = db.session.execute(
        select(Task.priority, func.count()).group_by(Task.priority)
    ).all()
    return {priority: total for priority, total in rows}


def count_by_category() -> dict[int, int]:
    rows = db.session.execute(
        select(Task.category_id, func.count()).group_by(Task.category_id)
    ).all()
    return {category_id: total for category_id, total in rows if category_id is not None}


def list_overdue_candidates() -> list[Task]:
    """Tasks com prazo vencido e status não final — o filtro roda no banco."""
    stmt = (
        select(Task)
        .where(Task.due_date.is_not(None))
        .where(Task.status.not_in(tuple(FINAL_STATUSES)))
        .order_by(Task.id)
    )
    return list(db.session.execute(stmt).scalars().all())


def count_created_since(momento: datetime) -> int:
    return db.session.execute(
        select(func.count()).select_from(Task).where(Task.created_at >= momento)
    ).scalar_one()


def count_done_since(momento: datetime) -> int:
    return db.session.execute(
        select(func.count())
        .select_from(Task)
        .where(Task.status == 'done', Task.updated_at >= momento)
    ).scalar_one()


def productivity_by_user() -> dict[int, tuple[int, int]]:
    """Total e concluídas por usuário, em uma consulta no lugar de uma por usuário."""
    rows = db.session.execute(
        select(
            Task.user_id,
            func.count(),
            func.sum(case((Task.status == 'done', 1), else_=0)),
        ).group_by(Task.user_id)
    ).all()
    return {
        user_id: (total, int(done or 0))
        for user_id, total, done in rows
        if user_id is not None
    }


def add(task: Task) -> None:
    db.session.add(task)


def remove(task: Task) -> None:
    db.session.delete(task)
