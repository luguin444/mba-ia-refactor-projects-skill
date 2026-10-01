from sqlalchemy import func, select

from database import db
from models.category import Category


def get(category_id):
    return db.session.get(Category, category_id)


def list_all(page=None):
    stmt = select(Category).order_by(Category.id)
    if page is not None:
        stmt = stmt.limit(page.limit).offset(page.offset)
    return db.session.scalars(stmt).all()


def count():
    return db.session.scalar(select(func.count(Category.id)))
