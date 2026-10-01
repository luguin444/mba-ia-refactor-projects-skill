import logging

FORMATO = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def configurar_logging(nivel="INFO"):
    logging.basicConfig(level=nivel, format=FORMATO)
