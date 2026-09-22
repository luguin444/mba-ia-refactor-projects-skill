"""Script para popular o banco com dados iniciais."""
from datetime import timedelta

from sqlalchemy import delete

from app import app, init_database
from database import db
from models.category import Category
from models.constants import TaskStatus, UserRole
from models.task import Task
from models.user import User
from utils.helpers import utc_now

USERS = [
    ('João Silva', 'joao@email.com', '1234', UserRole.ADMIN),
    ('Maria Santos', 'maria@email.com', 'abcd', UserRole.USER),
    ('Pedro Oliveira', 'pedro@email.com', 'pass', UserRole.MANAGER),
]

CATEGORIES = [
    ('Backend', 'Tarefas de backend', '#3498db'),
    ('Frontend', 'Tarefas de frontend', '#2ecc71'),
    ('DevOps', 'Tarefas de infraestrutura', '#e74c3c'),
    ('Bug', 'Correção de bugs', '#e67e22'),
]


def _tasks(users, categories):
    agora = utc_now()
    return [
        {'title': 'Implementar autenticação JWT', 'description': 'Adicionar autenticação real com JWT',
         'status': TaskStatus.PENDING, 'priority': 1, 'user_id': users[0].id,
         'category_id': categories[0].id, 'due_date': agora - timedelta(days=3)},
        {'title': 'Criar tela de login', 'description': 'Tela de login responsiva',
         'status': TaskStatus.IN_PROGRESS, 'priority': 2, 'user_id': users[1].id,
         'category_id': categories[1].id, 'due_date': agora + timedelta(days=5)},
        {'title': 'Configurar CI/CD', 'description': 'Pipeline com GitHub Actions',
         'status': TaskStatus.DONE, 'priority': 2, 'user_id': users[2].id,
         'category_id': categories[2].id, 'tags': 'devops,ci,github'},
        {'title': 'Corrigir bug no filtro de busca', 'description': 'Filtro não funciona com caracteres especiais',
         'status': TaskStatus.PENDING, 'priority': 1, 'user_id': users[0].id,
         'category_id': categories[3].id, 'due_date': agora - timedelta(days=1)},
        {'title': 'Adicionar paginação na API', 'description': 'Endpoints retornam todos os registros',
         'status': TaskStatus.PENDING, 'priority': 3, 'user_id': users[0].id,
         'category_id': categories[0].id, 'due_date': agora + timedelta(days=10)},
        {'title': 'Escrever testes unitários', 'description': 'Cobertura mínima de 80%',
         'status': TaskStatus.PENDING, 'priority': 2, 'user_id': users[1].id,
         'category_id': categories[0].id},
        {'title': 'Documentar API com Swagger', 'description': 'Gerar documentação automática',
         'status': TaskStatus.CANCELLED, 'priority': 4, 'user_id': users[2].id,
         'category_id': categories[0].id},
        {'title': 'Refatorar models', 'description': 'Melhorar organização dos models',
         'status': TaskStatus.IN_PROGRESS, 'priority': 3, 'user_id': users[1].id,
         'category_id': categories[0].id, 'tags': 'refactor,tech-debt'},
        {'title': 'Configurar monitoramento', 'description': 'Prometheus + Grafana',
         'status': TaskStatus.PENDING, 'priority': 4, 'user_id': users[2].id,
         'category_id': categories[2].id, 'due_date': agora + timedelta(days=20)},
        {'title': 'Melhorar validações de input', 'description': 'Usar marshmallow ou pydantic',
         'status': TaskStatus.PENDING, 'priority': 3, 'user_id': users[0].id,
         'category_id': categories[0].id, 'tags': 'improvement,validation'},
    ]


def seed_data() -> None:
    init_database(app)
    with app.app_context():
        for modelo in (Task, User, Category):
            db.session.execute(delete(modelo))
        db.session.commit()

        users = []
        for name, email, senha, role in USERS:
            user = User()
            user.name = name
            user.email = email
            user.set_password(senha)
            user.role = role.value
            db.session.add(user)
            users.append(user)

        categories = []
        for name, description, color in CATEGORIES:
            category = Category()
            category.name = name
            category.description = description
            category.color = color
            db.session.add(category)
            categories.append(category)

        db.session.commit()

        for dados in _tasks(users, categories):
            task = Task()
            task.title = dados['title']
            task.description = dados['description']
            task.status = dados['status'].value
            task.priority = dados['priority']
            task.user_id = dados['user_id']
            task.category_id = dados['category_id']
            task.due_date = dados.get('due_date')
            task.tags = dados.get('tags')
            db.session.add(task)

        db.session.commit()

        print('Seed concluído com sucesso!')
        print(f'  {len(users)} usuários')
        print(f'  {len(categories)} categorias')
        print(f'  {len(_tasks(users, categories))} tasks')


if __name__ == '__main__':
    seed_data()
