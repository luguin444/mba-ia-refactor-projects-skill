from flask import Flask
from flask_cors import CORS

from config import settings
from config.logging_config import configure_logging
from database import db, init_db, init_engine
from middlewares.error_handler import register_error_handlers
from routes.category_routes import category_bp
from routes.health_routes import health_bp
from routes.report_routes import report_bp
from routes.task_routes import task_bp
from routes.user_routes import user_bp

BLUEPRINTS = (health_bp, task_bp, user_bp, report_bp, category_bp)


def create_app():
    configure_logging(settings.LOG_LEVEL)

    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = settings.SECRET_KEY

    CORS(app, origins=settings.CORS_ORIGINS)
    init_engine(app)

    for blueprint in BLUEPRINTS:
        app.register_blueprint(blueprint)
    register_error_handlers(app)

    @app.cli.command('init-db')
    def init_db_command():
        """Cria o schema do banco."""
        init_db(app)

    return app


app = create_app()

if __name__ == '__main__':
    init_db(app)
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
