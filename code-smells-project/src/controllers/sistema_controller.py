"""Handlers de índice e health-check.

O health deixou de devolver `secret_key`, `debug` e `db_path` — exceção de contrato
declarada na Fase 2. Os contadores vêm dos models, não de SQL escrito aqui.
"""
from flask import jsonify

from src.config.settings import settings
from src.models import pedido_model, produto_model, usuario_model


def index():
    return jsonify({
        "mensagem": "Bem-vindo à API da Loja",
        "versao": settings.VERSAO,
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health",
        },
    })


def health():
    return jsonify({
        "status": "ok",
        "database": "connected",
        "counts": {
            "produtos": produto_model.contar(),
            "usuarios": usuario_model.contar(),
            "pedidos": pedido_model.contar(),
        },
        "versao": settings.VERSAO,
        "ambiente": settings.AMBIENTE,
    }), 200
