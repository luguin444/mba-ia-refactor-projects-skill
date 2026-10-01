from flask import Blueprint

from src.controllers import relatorio_controller
from src.middlewares.auth import requer_admin

relatorio_bp = Blueprint("relatorios", __name__)

relatorio_bp.add_url_rule("/relatorios/vendas", "relatorio_vendas", requer_admin(relatorio_controller.vendas),
                          methods=["GET"])
