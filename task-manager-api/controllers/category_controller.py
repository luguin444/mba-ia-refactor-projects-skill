"""Controller de Category."""
from flask import jsonify, request

from controllers.pagination import pagination_args
from services import category_service


def list_categories():
    return jsonify([
        {**category.to_dict(), 'task_count': total}
        for category, total in category_service.list_with_task_count(**pagination_args())
    ]), 200


def create_category():
    category = category_service.create_category(request.get_json())
    return jsonify(category.to_dict()), 201


def update_category(cat_id: int):
    category = category_service.update_category(cat_id, request.get_json())
    return jsonify(category.to_dict()), 200


def delete_category(cat_id: int):
    category_service.delete_category(cat_id)
    return jsonify({'message': 'Categoria deletada'}), 200
