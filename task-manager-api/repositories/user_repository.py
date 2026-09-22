"""Acesso a dados de User."""
from sqlalchemy import func, select

from database import db
from models.user import User


def list_all(*, limit: int | None = None, offset: int | None = None) -> list[User]:
    stmt = select(User).order_by(User.id)
    if offset:
        stmt = stmt.offset(offset)
    if limit is not None:
        stmt = stmt.limit(limit)
    return list(db.session.execute(stmt).scalars().all())


def get_by_id(user_id: int) -> User | None:
    return db.session.get(User, user_id)


def get_by_email(email: str) -> User | None:
    return db.session.execute(select(User).where(User.email == email)).scalars().first()


def count_all() -> int:
    return db.session.execute(select(func.count()).select_from(User)).scalar_one()


def add(user: User) -> None:
    db.session.add(user)


def remove(user: User) -> None:
    db.session.delete(user)
