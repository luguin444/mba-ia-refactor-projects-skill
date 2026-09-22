from database import db
from models.constants import DEFAULT_PRIORITY, FINAL_STATUSES, TaskStatus
from utils.helpers import format_date, utc_now


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=TaskStatus.PENDING.value)
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True
    )
    category_id = db.Column(
        db.Integer, db.ForeignKey('categories.id', ondelete='SET NULL'), nullable=True
    )
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', back_populates='tasks')
    category = db.relationship('Category', back_populates='tasks')

    def is_overdue(self) -> bool:
        """Task com prazo vencido que ainda não chegou a um status final."""
        return (
            self.due_date is not None
            and self.due_date < utc_now()
            and self.status not in FINAL_STATUSES
        )

    def tag_list(self) -> list[str]:
        return self.tags.split(',') if self.tags else []

    def to_dict(self, *, include_overdue: bool = False, include_relations: bool = False) -> dict:
        """Serializa a task.

        As três variações existem porque o contrato atual expõe três formatos
        distintos do mesmo recurso — ver `to_summary_dict` para o quarto.
        """
        data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'user_id': self.user_id,
            'category_id': self.category_id,
            'created_at': str(self.created_at),
            'updated_at': str(self.updated_at),
            'due_date': format_date(self.due_date),
            'tags': self.tag_list(),
        }
        if include_overdue:
            data['overdue'] = self.is_overdue()
        if include_relations:
            data['user_name'] = self.user.name if self.user else None
            data['category_name'] = self.category.name if self.category else None
        return data

    def to_summary_dict(self) -> dict:
        """Formato reduzido usado por `GET /users/<id>/tasks`."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'created_at': str(self.created_at),
            'due_date': format_date(self.due_date),
            'overdue': self.is_overdue(),
        }
