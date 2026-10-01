"""Script para popular o banco com dados iniciais"""
from datetime import timedelta

from sqlalchemy import delete, func, select

from app import app, db
from database import init_db
from models.category import Category
from models.task import Task
from models.user import User
from utils.helpers import utcnow


def seed_data():
    init_db(app)
    with app.app_context():

        db.session.execute(delete(Task))
        db.session.execute(delete(User))
        db.session.execute(delete(Category))
        db.session.commit()

        joao = User(name='João Silva', email='joao@email.com', role='admin')
        joao.set_password('1234')
        maria = User(name='Maria Santos', email='maria@email.com', role='user')
        maria.set_password('abcd')
        pedro = User(name='Pedro Oliveira', email='pedro@email.com', role='manager')
        pedro.set_password('pass')
        db.session.add_all([joao, maria, pedro])
        db.session.commit()

        backend = Category(name='Backend', description='Tarefas de backend', color='#3498db')
        frontend = Category(name='Frontend', description='Tarefas de frontend', color='#2ecc71')
        devops = Category(name='DevOps', description='Tarefas de infraestrutura', color='#e74c3c')
        bug = Category(name='Bug', description='Correção de bugs', color='#e67e22')
        db.session.add_all([backend, frontend, devops, bug])
        db.session.commit()

        now = utcnow()
        tasks_data = [
            {'title': 'Implementar autenticação JWT', 'description': 'Adicionar autenticação real com JWT', 'status': 'pending', 'priority': 1, 'user_id': joao.id, 'category_id': backend.id, 'due_date': now - timedelta(days=3)},
            {'title': 'Criar tela de login', 'description': 'Tela de login responsiva', 'status': 'in_progress', 'priority': 2, 'user_id': maria.id, 'category_id': frontend.id, 'due_date': now + timedelta(days=5)},
            {'title': 'Configurar CI/CD', 'description': 'Pipeline com GitHub Actions', 'status': 'done', 'priority': 2, 'user_id': pedro.id, 'category_id': devops.id, 'tags': 'devops,ci,github'},
            {'title': 'Corrigir bug no filtro de busca', 'description': 'Filtro não funciona com caracteres especiais', 'status': 'pending', 'priority': 1, 'user_id': joao.id, 'category_id': bug.id, 'due_date': now - timedelta(days=1)},
            {'title': 'Adicionar paginação na API', 'description': 'Endpoints retornam todos os registros', 'status': 'pending', 'priority': 3, 'user_id': joao.id, 'category_id': backend.id, 'due_date': now + timedelta(days=10)},
            {'title': 'Escrever testes unitários', 'description': 'Cobertura mínima de 80%', 'status': 'pending', 'priority': 2, 'user_id': maria.id, 'category_id': backend.id},
            {'title': 'Documentar API com Swagger', 'description': 'Gerar documentação automática', 'status': 'cancelled', 'priority': 4, 'user_id': pedro.id, 'category_id': backend.id},
            {'title': 'Refatorar models', 'description': 'Melhorar organização dos models', 'status': 'in_progress', 'priority': 3, 'user_id': maria.id, 'category_id': backend.id, 'tags': 'refactor,tech-debt'},
            {'title': 'Configurar monitoramento', 'description': 'Prometheus + Grafana', 'status': 'pending', 'priority': 4, 'user_id': pedro.id, 'category_id': devops.id, 'due_date': now + timedelta(days=20)},
            {'title': 'Melhorar validações de input', 'description': 'Usar marshmallow ou pydantic', 'status': 'pending', 'priority': 3, 'user_id': joao.id, 'category_id': backend.id, 'tags': 'improvement,validation'},
        ]
        db.session.add_all([Task(**task_data) for task_data in tasks_data])
        db.session.commit()

        def count(model):
            return db.session.scalar(select(func.count()).select_from(model))

        print("Seed concluído com sucesso!")
        print(f"  {count(User)} usuários")
        print(f"  {count(Category)} categorias")
        print(f"  {count(Task)} tasks")


if __name__ == '__main__':
    seed_data()
