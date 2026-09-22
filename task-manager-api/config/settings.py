"""Configuração lida do ambiente. Único lugar com valor que varia por ambiente."""
import logging
import os

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Carrega o .env local, quando existir. Variáveis já definidas no ambiente
# vencem o arquivo.
load_dotenv()


def _secret_key() -> str:
    """Lê SECRET_KEY do ambiente; sem a variável, gera uma efêmera e avisa.

    A chave gerada muda a cada restart, então toda sessão assinada com ela é
    invalidada no próximo boot. Não há fallback literal: um segredo fixo no
    código é o mesmo segredo hardcoded com uma indireção a mais.
    """
    chave = os.environ.get('SECRET_KEY')
    if chave:
        return chave
    logger.warning(
        'SECRET_KEY ausente: usando chave efêmera gerada no boot. '
        'Sessões assinadas não sobrevivem ao restart. Defina SECRET_KEY em produção.'
    )
    return os.urandom(32).hex()


def _cors_origins() -> list[str] | str:
    """Origens permitidas. Sem a variável, libera tudo e avisa.

    O default permissivo existe para o projeto rodar recém-clonado; o aviso
    existe para que ninguém suba assim em produção sem perceber.
    """
    brutas = os.environ.get('CORS_ORIGINS', '').strip()
    if not brutas:
        logger.warning(
            'CORS_ORIGINS ausente: liberando todas as origens. '
            'Defina a lista de origens permitidas em produção.'
        )
        return '*'
    return [origem.strip() for origem in brutas.split(',') if origem.strip()]


class Settings:
    SECRET_KEY = _secret_key()
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI', 'sqlite:///tasks.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'
    HOST = os.environ.get('HOST', '127.0.0.1')
    PORT = int(os.environ.get('PORT', '5000'))
    CORS_ORIGINS = _cors_origins()
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()


settings = Settings()
