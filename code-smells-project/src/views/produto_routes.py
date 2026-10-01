from flask import Blueprint

from src.controllers import produto_controller
from src.middlewares.auth import requer_admin

produto_bp = Blueprint("produtos", __name__)

produto_bp.add_url_rule("/produtos", "listar_produtos", produto_controller.listar, methods=["GET"])
produto_bp.add_url_rule("/produtos/busca", "buscar_produtos", produto_controller.pesquisar, methods=["GET"])
produto_bp.add_url_rule("/produtos/<int:produto_id>", "buscar_produto", produto_controller.buscar, methods=["GET"])
produto_bp.add_url_rule("/produtos", "criar_produto", requer_admin(produto_controller.criar), methods=["POST"])
produto_bp.add_url_rule("/produtos/<int:produto_id>", "atualizar_produto",
                        requer_admin(produto_controller.atualizar), methods=["PUT"])
produto_bp.add_url_rule("/produtos/<int:produto_id>", "deletar_produto",
                        requer_admin(produto_controller.remover), methods=["DELETE"])
