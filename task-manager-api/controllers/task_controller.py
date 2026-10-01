from flask import jsonify, request

from controllers.pagination import page_from_request
from middlewares.auth import current_actor
from services import task_service


def list_tasks():
    return jsonify(task_service.list_board(page_from_request())), 200


def get_task(task_id):
    return jsonify(task_service.get_detail(task_id)), 200


def create_task():
    return jsonify(task_service.create(request.get_json())), 201


def update_task(task_id):
    task = task_service.get_for_write(task_id, current_actor())
    return jsonify(task_service.update(task, request.get_json())), 200


def delete_task(task_id):
    task_service.delete(task_id, current_actor())
    return jsonify({'message': 'Task deletada com sucesso'}), 200


def search_tasks():
    priority = request.args.get('priority', '')
    user_id = request.args.get('user_id', '')
    tasks = task_service.search(
        text=request.args.get('q', ''),
        status=request.args.get('status', ''),
        priority=int(priority) if priority else None,
        user_id=int(user_id) if user_id else None,
        page=page_from_request(),
    )
    return jsonify(tasks), 200


def task_stats():
    return jsonify(task_service.stats()), 200
