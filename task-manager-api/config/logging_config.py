"""Configuração do logging da aplicação."""
import logging

from config.settings import settings


def configure_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
        format='%(asctime)s %(levelname)-8s %(name)s | %(message)s',
    )
