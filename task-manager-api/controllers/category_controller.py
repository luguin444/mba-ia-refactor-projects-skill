from flask import jsonify, request

from controllers.pagination import page_from_request
from services import category_service


def list_categories():
    return jsonify(category_service.list_with_task_count(page_from_request())), 200


def create_category():
    return jsonify(category_service.create(request.get_json())), 201


def update_category(cat_id):
    category = category_service.get_or_404(cat_id)
    return jsonify(category_service.update(category, request.get_json())), 200


def delete_category(cat_id):
    category_service.delete(cat_id)
    return jsonify({'message': 'Categoria deletada'}), 200
