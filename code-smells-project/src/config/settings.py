"""Única fonte de valores que variam por ambiente. Não importa nenhuma outra camada."""
import logging
import os

_logger = logging.getLogger(__name__)


def _flag(nome: str, padrao: str = "false") -> bool:
    return os.getenv(nome, padrao).strip().lower() in ("1", "true", "yes", "on")


def _secret_key() -> str:
    """Lê SECRET_KEY do ambiente; sem ela, gera uma efêmera e avisa em voz alta.

    A aplicação sobe sem configuração para não exigir `.env` em desenvolvimento,
    mas a chave muda a cada restart e toda sessão assinada é invalidada. Em
    produção, defina SECRET_KEY — veja `.env.example`.
    """
    chave = os.environ.get("SECRET_KEY")
    if chave:
        return chave

    _logger.warning(
        "SECRET_KEY ausente no ambiente: usando chave efêmera gerada no boot. "
        "Sessões assinadas não sobrevivem ao restart. Defina SECRET_KEY em produção."
    )
    return os.urandom(32).hex()


class Settings:
    SECRET_KEY = _secret_key()

    DEBUG = _flag("DEBUG")
    DATABASE_PATH = os.getenv("DATABASE_PATH", "loja.db")
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", "5000"))

    # Vazio = nenhuma origem cross-site liberada.
    CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Semear dados de exemplo no boot. Explícito, nunca disparado por obter conexão.
    SEED_ON_BOOT = _flag("SEED_ON_BOOT", "true")

    AMBIENTE = os.getenv("AMBIENTE", "producao")
    VERSAO = "1.0.0"


settings = Settings()
