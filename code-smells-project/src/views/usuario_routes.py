from flask import Blueprint

from src.controllers import usuario_controller
from src.middlewares.auth import requer_admin, requer_dono_ou_admin

usuario_bp = Blueprint("usuarios", __name__)

usuario_bp.add_url_rule("/usuarios", "listar_usuarios", requer_admin(usuario_controller.listar), methods=["GET"])
usuario_bp.add_url_rule("/usuarios/<int:usuario_id>", "buscar_usuario",
                        requer_dono_ou_admin("usuario_id")(usuario_controller.buscar), methods=["GET"])
usuario_bp.add_url_rule("/usuarios", "criar_usuario", usuario_controller.criar, methods=["POST"])
usuario_bp.add_url_rule("/login", "login", usuario_controller.login, methods=["POST"])
