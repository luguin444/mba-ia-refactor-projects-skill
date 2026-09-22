"""Configuração de logging da aplicação. Substitui os `print` espalhados pelo projeto."""
import logging

from src.config.settings import settings


def configurar_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    )
