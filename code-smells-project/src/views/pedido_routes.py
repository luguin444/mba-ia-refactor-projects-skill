from flask import Blueprint

from src.controllers import pedido_controller
from src.middlewares.auth import requer_admin, requer_autenticacao, requer_dono_ou_admin

pedido_bp = Blueprint("pedidos", __name__)

# POST /pedidos: credencial aqui; a checagem de dono do `usuario_id` do corpo fica no controller.
pedido_bp.add_url_rule("/pedidos", "criar_pedido", requer_autenticacao(pedido_controller.criar), methods=["POST"])
pedido_bp.add_url_rule("/pedidos", "listar_todos_pedidos", requer_admin(pedido_controller.listar), methods=["GET"])
pedido_bp.add_url_rule("/pedidos/usuario/<int:usuario_id>", "listar_pedidos_usuario",
                       requer_dono_ou_admin("usuario_id")(pedido_controller.listar_por_usuario), methods=["GET"])
pedido_bp.add_url_rule("/pedidos/<int:pedido_id>/status", "atualizar_status_pedido",
                       requer_admin(pedido_controller.atualizar_status), methods=["PUT"])
