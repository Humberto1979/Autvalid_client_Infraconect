from flask import Flask

from .routes.health import bp as health_bp
from .routes.records import bp as records_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(health_bp)
    app.register_blueprint(records_bp)
    return app


# Gunicorn aponta para `app.main:app`.
app = create_app()