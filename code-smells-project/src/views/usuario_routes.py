"""Registro das rotas de usuário e login. Caminhos idênticos aos originais."""
from flask import Blueprint

from src.controllers import usuario_controller

usuario_bp = Blueprint("usuarios", __name__)

usuario_bp.add_url_rule("/usuarios", "listar_usuarios", usuario_controller.listar, methods=["GET"])
usuario_bp.add_url_rule("/usuarios/<int:id>", "buscar_usuario", usuario_controller.buscar, methods=["GET"])
usuario_bp.add_url_rule("/usuarios", "criar_usuario", usuario_controller.criar, methods=["POST"])
usuario_bp.add_url_rule("/login", "login", usuario_controller.login, methods=["POST"])
