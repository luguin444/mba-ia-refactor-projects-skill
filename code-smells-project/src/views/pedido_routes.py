"""Registro das rotas de pedido. Caminhos idênticos aos originais."""
from flask import Blueprint

from src.controllers import pedido_controller

pedido_bp = Blueprint("pedidos", __name__)

pedido_bp.add_url_rule("/pedidos", "criar_pedido", pedido_controller.criar, methods=["POST"])
pedido_bp.add_url_rule("/pedidos", "listar_todos_pedidos", pedido_controller.listar, methods=["GET"])
pedido_bp.add_url_rule("/pedidos/usuario/<int:usuario_id>", "listar_pedidos_usuario",
                       pedido_controller.listar_por_usuario, methods=["GET"])
pedido_bp.add_url_rule("/pedidos/<int:pedido_id>/status", "atualizar_status_pedido",
                       pedido_controller.atualizar_status, methods=["PUT"])
