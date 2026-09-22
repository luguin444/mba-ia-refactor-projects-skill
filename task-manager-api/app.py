"""Composition root: lê a config, monta as dependências e registra as rotas."""
from flask import Flask
from flask_cors import CORS

from config.logging_config import configure_logging
from config.settings import settings
from database import db
from middlewares.error_handler import register_error_handlers
from routes.category_routes import category_bp
from routes.health_routes import health_bp
from routes.report_routes import report_bp
from routes.task_routes import task_bp
from routes.user_routes import user_bp

BLUEPRINTS = (health_bp, task_bp, user_bp, category_bp, report_bp)


def create_app() -> Flask:
    configure_logging()

    app = Flask(__name__)
    app.config.from_object(settings)

    CORS(app, origins=settings.CORS_ORIGINS)
    db.init_app(app)

    for blueprint in BLUEPRINTS:
        app.register_blueprint(blueprint)

    register_error_handlers(app)
    return app


def init_database(app: Flask) -> None:
    """Cria o schema. Acionada explicitamente, nunca por import."""
    with app.app_context():
        db.create_all()


app = create_app()


if __name__ == '__main__':
    init_database(app)
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
