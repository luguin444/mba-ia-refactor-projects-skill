from database import db
from models.constants import (
    DEFAULT_PRIORITY,
    FINISHED_STATUSES,
    MAX_PRIORITY,
    MIN_PRIORITY,
    TaskStatus,
    VALID_STATUSES,
)
from utils.helpers import utcnow


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=TaskStatus.PENDING.value)
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', back_populates='tasks')
    category = db.relationship('Category', back_populates='tasks')

    @staticmethod
    def validate_status(new_status):
        return new_status in VALID_STATUSES

    @staticmethod
    def validate_priority(priority):
        return MIN_PRIORITY <= priority <= MAX_PRIORITY

    def is_overdue(self):
        return (
            self.due_date is not None
            and self.due_date < utcnow()
            and self.status not in FINISHED_STATUSES
        )

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'user_id': self.user_id,
            'category_id': self.category_id,
            'created_at': str(self.created_at),
            'updated_at': str(self.updated_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'tags': self.tags.split(',') if self.tags else [],
        }

    def to_detail_dict(self):
        """GET /tasks/<id>: o recurso com o indicador de atraso."""
        return {**self.to_dict(), 'overdue': self.is_overdue()}

    def to_board_dict(self):
        """GET /tasks: o quadro, com os nomes de responsável e categoria."""
        return {
            **self.to_detail_dict(),
            'user_name': self.user.name if self.user else None,
            'category_name': self.category.name if self.category else None,
        }

    def to_owner_list_dict(self):
        """GET /users/<id>/tasks: recorte sem ids de relacionamento, tags nem updated_at."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'created_at': str(self.created_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'overdue': self.is_overdue(),
        }

    def to_overdue_dict(self):
        """Item da lista de atrasadas no relatório geral."""
        return {
            'id': self.id,
            'title': self.title,
            'due_date': str(self.due_date),
            'days_overdue': (utcnow() - self.due_date).days,
        }
