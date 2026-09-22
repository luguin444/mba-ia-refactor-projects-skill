"""Registro da rota de relatório. Caminho idêntico ao original."""
from flask import Blueprint

from src.controllers import relatorio_controller

relatorio_bp = Blueprint("relatorios", __name__)

relatorio_bp.add_url_rule("/relatorios/vendas", "relatorio_vendas",
                          relatorio_controller.vendas, methods=["GET"])
