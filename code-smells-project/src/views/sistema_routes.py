from flask import Blueprint

from src.controllers import sistema_controller

sistema_bp = Blueprint("sistema", __name__)

sistema_bp.add_url_rule("/", "index", sistema_controller.index, methods=["GET"])
sistema_bp.add_url_rule("/health", "health_check", sistema_controller.health, methods=["GET"])
