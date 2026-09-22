"""Controller de User."""
from flask import jsonify, request

from controllers.pagination import pagination_args
from services import task_service, user_service


def list_users():
    users = user_service.list_users(**pagination_args())
    return jsonify([
        {**user.to_dict(), 'task_count': len(user.tasks)} for user in users
    ]), 200


def get_user(user_id: int):
    user = user_service.get_user(user_id)
    data = user.to_dict()
    data['tasks'] = [task.to_dict() for task in task_service.list_tasks_of_user(user_id)]
    return jsonify(data), 200


def create_user():
    user = user_service.create_user(request.get_json())
    return jsonify(user.to_dict()), 201


def update_user(user_id: int):
    user = user_service.update_user(user_id, request.get_json())
    return jsonify(user.to_dict()), 200


def delete_user(user_id: int):
    user_service.delete_user(user_id)
    return jsonify({'message': 'Usuário deletado com sucesso'}), 200


def get_user_tasks(user_id: int):
    user_service.get_user(user_id)
    tasks = task_service.list_tasks_of_user(user_id)
    return jsonify([task.to_summary_dict() for task in tasks]), 200


def login():
    user = user_service.authenticate(request.get_json())
    return jsonify({
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': user_service.issue_token(user),
    }), 200
