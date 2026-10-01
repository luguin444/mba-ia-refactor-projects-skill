import logging

from flask import jsonify

from src.config.settings import settings
from src.middlewares.error_handler import MENSAGEM_ERRO_INTERNO
from src.models import sistema_model
from src.models.constants import VERSAO_API

logger = logging.getLogger(__name__)


def index():
    return jsonify({
        "mensagem": "Bem-vindo à API da Loja",
        "versao": VERSAO_API,
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
    # Captura local deliberada: o /health tem formato de erro próprio ({status, detalhes}).
    try:
        contagens = sistema_model.contagens()
    except Exception:
        logger.exception("health check falhou")
        return jsonify({"status": "erro", "detalhes": MENSAGEM_ERRO_INTERNO}), 500
    return jsonify({
        "status": "ok",
        "database": "connected",
        "counts": contagens,
        "versao": VERSAO_API,
        "ambiente": settings.APP_ENV,
        "db_path": settings.DATABASE_PATH,
        "debug": settings.DEBUG,
    }), 200
