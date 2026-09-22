"""Composition root: lê config, monta as dependências, registra rotas e sobe o servidor.

Nenhuma rota é definida aqui e nenhuma lógica roda aqui.
"""
from flask import Flask
from flask_cors import CORS

from src.config.logging_config import configurar_logging
from src.config.settings import settings
from src.database.connection import abrir_conexao, fechar_conexao
from src.database.schema import criar_schema
from src.database.seed import semear
from src.middlewares.error_handler import registrar_error_handlers
from src.views.pedido_routes import pedido_bp
from src.views.produto_routes import produto_bp
from src.views.relatorio_routes import relatorio_bp
from src.views.sistema_routes import sistema_bp
from src.views.usuario_routes import usuario_bp

BLUEPRINTS = (produto_bp, usuario_bp, pedido_bp, relatorio_bp, sistema_bp)


def inicializar_banco() -> None:
    """Cria o schema e, se configurado, semeia. Explícito — não acontece por obter conexão."""
    conexao = abrir_conexao()
    try:
        criar_schema(conexao)
        if settings.SEED_ON_BOOT:
            semear(conexao)
    finally:
        conexao.close()


def create_app() -> Flask:
    configurar_logging()

    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["DEBUG"] = settings.DEBUG

    CORS(app, origins=settings.CORS_ORIGINS)

    inicializar_banco()
    app.teardown_appcontext(fechar_conexao)

    for blueprint in BLUEPRINTS:
        app.register_blueprint(blueprint)

    registrar_error_handlers(app)
    return app


app = create_app()

if __name__ == "__main__":
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
