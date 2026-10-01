from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from database import db
from models.user import User


def get(user_id):
    return db.session.get(User, user_id)


def get_by_email(email):
    return db.session.scalars(select(User).where(User.email == email)).first()


def list_all(page=None):
    stmt = select(User).order_by(User.id)
    if page is not None:
        stmt = stmt.limit(page.limit).offset(page.offset)
    return db.session.scalars(stmt).all()


def list_with_tasks():
    return db.session.scalars(select(User).options(selectinload(User.tasks)).order_by(User.id)).all()


def count():
    return db.session.scalar(select(func.count(User.id)))
