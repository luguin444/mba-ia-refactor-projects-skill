import logging
import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()

_logger = logging.getLogger(__name__)


def _secret_key() -> str:
    """Lê SECRET_KEY do ambiente; sem a variável, gera uma chave efêmera e avisa.

    A chave efêmera muda a cada restart, então todo token emitido antes dele deixa de valer.
    """
    key = os.environ.get("SECRET_KEY")
    if key:
        return key
    _logger.warning(
        "SECRET_KEY ausente: usando chave efêmera gerada no boot. "
        "Tokens emitidos não sobrevivem ao restart. Defina SECRET_KEY em produção."
    )
    return os.urandom(32).hex()


def _list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings:
    SECRET_KEY = _secret_key()
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", "5000"))
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///tasks.db")
    # Default "*" preserva o comportamento atual; quais origens liberar é decisão de produto.
    CORS_ORIGINS = _list(os.getenv("CORS_ORIGINS", "*"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    TOKEN_TTL = timedelta(hours=int(os.getenv("TOKEN_TTL_HOURS", "12")))


settings = Settings()
