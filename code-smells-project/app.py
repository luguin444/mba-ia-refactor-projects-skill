"""Composition root: lê config, monta dependências, registra rotas e middlewares."""
import logging

from flask import Flask
from flask_cors import CORS

from src.config.logging_config import configurar_logging
from src.config.settings import settings
from src.database import connection
from src.database.schema import criar_schema
from src.database.seed import popular_dados_exemplo
from src.middlewares.error_handler import register_error_handlers
from src.services import pedido_service
from src.services.notificacao_service import NotificacaoService
from src.views.pedido_routes import pedido_bp
from src.views.produto_routes import produto_bp
from src.views.relatorio_routes import relatorio_bp
from src.views.sistema_routes import sistema_bp
from src.views.usuario_routes import usuario_bp

logger = logging.getLogger(__name__)


def _avisos_de_configuracao():
    if settings.SECRET_KEY_EFEMERA:
        logger.warning("SECRET_KEY ausente: usando chave efêmera gerada no boot. "
                       "Tokens emitidos não sobrevivem ao restart. Defina SECRET_KEY em produção.")
    if settings.CORS_ORIGINS == "*":
        logger.warning("CORS_ORIGINS não definido: CORS liberado para todas as origens.")


def create_app():
    configurar_logging(settings.LOG_LEVEL)
    _avisos_de_configuracao()

    app = Flask(__name__)
    app.config.update(SECRET_KEY=settings.SECRET_KEY, DEBUG=settings.DEBUG)
    CORS(app, origins=settings.CORS_ORIGINS)

    connection.init_app(app)
    register_error_handlers(app)
    for blueprint in (sistema_bp, produto_bp, usuario_bp, pedido_bp, relatorio_bp):
        app.register_blueprint(blueprint)

    pedido_service.configurar_notificacao(NotificacaoService())

    with app.app_context():
        criar_schema()
        if settings.SEED_ON_BOOT:
            popular_dados_exemplo()

    return app


app = create_app()

if __name__ == "__main__":
    logger.info("servidor iniciado em http://%s:%s", settings.HOST, settings.PORT)
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
