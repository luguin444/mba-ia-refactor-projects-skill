"""Handler HTTP do relatório de vendas."""
from flask import jsonify

from src.services import relatorio_service


def vendas():
    return jsonify({"dados": relatorio_service.vendas(), "sucesso": True}), 200
