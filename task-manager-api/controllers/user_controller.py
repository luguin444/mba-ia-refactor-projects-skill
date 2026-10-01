from flask import jsonify, request

from controllers.pagination import page_from_request
from middlewares.auth import current_actor
from services import user_service


def list_users():
    return jsonify(user_service.list_with_task_count(page_from_request())), 200


def get_user(user_id):
    return jsonify(user_service.get_with_tasks(user_id)), 200


def create_user():
    return jsonify(user_service.create(request.get_json())), 201


def update_user(user_id):
    user = user_service.get_or_404(user_id)
    return jsonify(user_service.update(user, request.get_json(), current_actor())), 200


def delete_user(user_id):
    user_service.delete(user_id)
    return jsonify({'message': 'Usuário deletado com sucesso'}), 200


def get_user_tasks(user_id):
    return jsonify(user_service.list_tasks(user_id)), 200


def login():
    user, token = user_service.authenticate(request.get_json())
    return jsonify({'message': 'Login realizado com sucesso', 'user': user, 'token': token}), 200
