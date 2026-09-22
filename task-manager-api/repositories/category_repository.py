"""Acesso a dados de Category."""
from sqlalchemy import func, select

from database import db
from models.category import Category


def list_all(*, limit: int | None = None, offset: int | None = None) -> list[Category]:
    stmt = select(Category).order_by(Category.id)
    if offset:
        stmt = stmt.offset(offset)
    if limit is not None:
        stmt = stmt.limit(limit)
    return list(db.session.execute(stmt).scalars().all())


def get_by_id(category_id: int) -> Category | None:
    return db.session.get(Category, category_id)


def count_all() -> int:
    return db.session.execute(select(func.count()).select_from(Category)).scalar_one()


def add(category: Category) -> None:
    db.session.add(category)


def remove(category: Category) -> None:
    db.session.delete(category)
