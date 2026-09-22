"""Registro das rotas de índice e health-check.

As rotas `/admin/query` e `/admin/reset-db` não foram reimplementadas: executor de SQL
arbitrário e reset de banco sem autenticação não têm versão segura. Remoção declarada
como exceção de contrato na Fase 2.
"""
from flask import Blueprint

from src.controllers import sistema_controller

sistema_bp = Blueprint("sistema", __name__)

sistema_bp.add_url_rule("/", "index", sistema_controller.index, methods=["GET"])
sistema_bp.add_url_rule("/health", "health_check", sistema_controller.health, methods=["GET"])
