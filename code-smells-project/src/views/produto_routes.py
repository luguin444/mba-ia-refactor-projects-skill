"""Registro das rotas de produto. Caminhos idênticos aos originais."""
from flask import Blueprint

from src.controllers import produto_controller

produto_bp = Blueprint("produtos", __name__)

produto_bp.add_url_rule("/produtos", "listar_produtos", produto_controller.listar, methods=["GET"])
produto_bp.add_url_rule("/produtos/busca", "buscar_produtos", produto_controller.pesquisar, methods=["GET"])
produto_bp.add_url_rule("/produtos/<int:id>", "buscar_produto", produto_controller.buscar, methods=["GET"])
produto_bp.add_url_rule("/produtos", "criar_produto", produto_controller.criar, methods=["POST"])
produto_bp.add_url_rule("/produtos/<int:id>", "atualizar_produto", produto_controller.atualizar, methods=["PUT"])
produto_bp.add_url_rule("/produtos/<int:id>", "deletar_produto", produto_controller.deletar, methods=["DELETE"])
