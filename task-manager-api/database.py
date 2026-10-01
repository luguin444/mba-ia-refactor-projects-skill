import sqlite3

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event

db = SQLAlchemy()


def _enable_foreign_keys(dbapi_connection, _connection_record):
    # SQLite só aplica FOREIGN KEY com a pragma ligada em cada conexão.
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def init_engine(app):
    db.init_app(app)
    with app.app_context():
        event.listen(db.engine, "connect", _enable_foreign_keys)


def init_db(app):
    """Cria o schema. Chamado explicitamente pelo entry point, pelo seed ou por `flask init-db`."""
    with app.app_context():
        import models  # noqa: F401 — registra as tabelas no metadata

        db.create_all()
