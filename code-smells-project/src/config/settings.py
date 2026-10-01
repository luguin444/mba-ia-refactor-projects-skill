import os


def _bool(nome, padrao):
    return os.getenv(nome, str(padrao)).strip().lower() in ("1", "true", "yes")


def _secret_key():
    """Lê SECRET_KEY do ambiente; sem a variável, gera uma chave efêmera.

    A chave efêmera muda a cada restart e invalida todo token emitido antes.
    O composition root avisa no boot quando isso acontece.
    """
    chave = os.environ.get("SECRET_KEY")
    if chave:
        return chave, False
    return os.urandom(32).hex(), True


def _cors_origins():
    bruto = os.getenv("CORS_ORIGINS", "*").strip()
    if bruto == "*":
        return "*"
    return [origem.strip() for origem in bruto.split(",") if origem.strip()]


class Settings:
    SECRET_KEY, SECRET_KEY_EFEMERA = _secret_key()
    DEBUG = _bool("DEBUG", False)
    APP_ENV = os.getenv("APP_ENV", "producao")
    DATABASE_PATH = os.getenv("DATABASE_PATH", "loja.db")
    SEED_ON_BOOT = _bool("SEED_ON_BOOT", True)
    CORS_ORIGINS = _cors_origins()
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", "5000"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    TOKEN_TTL_HORAS = int(os.getenv("TOKEN_TTL_HORAS", "12"))


settings = Settings()
