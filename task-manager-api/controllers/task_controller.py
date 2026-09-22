"""Controller de Task: lê a requisição, chama o serviço, monta a resposta."""
from flask import jsonify, request

from controllers.pagination import pagination_args
from services import task_service


def list_tasks():
    tasks = task_service.list_tasks(**pagination_args())
    return jsonify([
        task.to_dict(include_overdue=True, include_relations=True) for task in tasks
    ]), 200


def get_task(task_id: int):
    task = task_service.get_task(task_id)
    return jsonify(task.to_dict(include_overdue=True)), 200


def create_task():
    task = task_service.create_task(request.get_json())
    return jsonify(task.to_dict()), 201


def update_task(task_id: int):
    task = task_service.update_task(task_id, request.get_json())
    return jsonify(task.to_dict()), 200


def delete_task(task_id: int):
    task_service.delete_task(task_id)
    return jsonify({'message': 'Task deletada com sucesso'}), 200


def search_tasks():
    priority = request.args.get('priority', '')
    user_id = request.args.get('user_id', '')
    tasks = task_service.search_tasks(
        termo=request.args.get('q', ''),
        status=request.args.get('status', ''),
        priority=int(priority) if priority else None,
        user_id=int(user_id) if user_id else None,
        **pagination_args(),
    )
    return jsonify([task.to_dict() for task in tasks]), 200


def task_stats():
    return jsonify(task_service.build_stats()), 200
