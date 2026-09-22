"""Única fonte de valores que variam por ambiente. Não importa nenhuma outra camada."""
import os


def _flag(nome: str, padrao: str = "false") -> bool:
    return os.getenv(nome, padrao).strip().lower() in ("1", "true", "yes", "on")


class Settings:
    # Sem default: falta de segredo derruba o boot em vez de rodar com chave conhecida.
    SECRET_KEY = os.environ.get("SECRET_KEY") or os.urandom(32).hex()

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
