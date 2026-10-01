from flask import Blueprint

from controllers import category_controller
from middlewares.auth import require_admin

category_bp = Blueprint('categories', __name__)

# Leitura pública (catálogo sem dado pessoal); escrita só admin, pois categoria não tem dono e o cadastro é público.
category_bp.add_url_rule('/categories', view_func=category_controller.list_categories, methods=['GET'])
category_bp.add_url_rule('/categories', view_func=require_admin(category_controller.create_category), methods=['POST'])
category_bp.add_url_rule(
    '/categories/<int:cat_id>', view_func=require_admin(category_controller.update_category), methods=['PUT']
)
category_bp.add_url_rule(
    '/categories/<int:cat_id>', view_func=require_admin(category_controller.delete_category), methods=['DELETE']
)
