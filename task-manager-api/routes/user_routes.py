from flask import Blueprint

from controllers import user_controller
from middlewares.auth import require_admin, require_owner_or_admin

user_bp = Blueprint('users', __name__)

owner_or_admin = require_owner_or_admin('user_id')

user_bp.add_url_rule('/users', view_func=require_admin(user_controller.list_users), methods=['GET'])
user_bp.add_url_rule('/users/<int:user_id>', view_func=owner_or_admin(user_controller.get_user), methods=['GET'])
# Público: o cadastro é o único caminho de entrada no sistema.
user_bp.add_url_rule('/users', view_func=user_controller.create_user, methods=['POST'])
user_bp.add_url_rule('/users/<int:user_id>', view_func=owner_or_admin(user_controller.update_user), methods=['PUT'])
user_bp.add_url_rule('/users/<int:user_id>', view_func=owner_or_admin(user_controller.delete_user), methods=['DELETE'])
user_bp.add_url_rule('/users/<int:user_id>/tasks', view_func=owner_or_admin(user_controller.get_user_tasks), methods=['GET'])
# Público: emite a credencial.
user_bp.add_url_rule('/login', view_func=user_controller.login, methods=['POST'])
