from sqlalchemy import func, or_, select
from sqlalchemy.orm import joinedload

from database import db
from models.task import Task


def _paginate(stmt, page):
    if page is not None:
        stmt = stmt.limit(page.limit).offset(page.offset)
    return stmt


def get(task_id):
    return db.session.get(Task, task_id)


def list_all(page=None):
    stmt = select(Task).order_by(Task.id)
    return db.session.scalars(_paginate(stmt, page)).all()


def list_with_relations(page=None):
    stmt = (
        select(Task)
        .options(joinedload(Task.user), joinedload(Task.category))
        .order_by(Task.id)
    )
    return db.session.scalars(_paginate(stmt, page)).unique().all()


def list_by_user(user_id):
    return db.session.scalars(select(Task).where(Task.user_id == user_id).order_by(Task.id)).all()


def search(text=None, status=None, priority=None, user_id=None, page=None):
    stmt = select(Task)
    if text:
        pattern = f'%{text}%'
        stmt = stmt.where(or_(Task.title.like(pattern), Task.description.like(pattern)))
    if status:
        stmt = stmt.where(Task.status == status)
    if priority is not None:
        stmt = stmt.where(Task.priority == priority)
    if user_id is not None:
        stmt = stmt.where(Task.user_id == user_id)
    return db.session.scalars(_paginate(stmt.order_by(Task.id), page)).all()


def _count(*conditions):
    return db.session.scalar(select(func.count(Task.id)).where(*conditions))


def _count_grouped_by(column):
    """{valor da coluna: total de tasks} numa query só."""
    return dict(db.session.execute(select(column, func.count(Task.id)).group_by(column)).all())


def count():
    return _count()


def count_created_since(moment):
    return _count(Task.created_at >= moment)


def count_with_status_updated_since(status, moment):
    return _count(Task.status == status, Task.updated_at >= moment)


def count_by_status():
    return _count_grouped_by(Task.status)


def count_by_priority():
    return _count_grouped_by(Task.priority)


def count_by_user():
    return _count_grouped_by(Task.user_id)


def count_by_category():
    return _count_grouped_by(Task.category_id)
