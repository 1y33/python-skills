import logging

_FORMAT = "%(asctime)s %(levelname)-7s [%(name)s] %(message)s"


def configure_logging(service: str, level: str = "INFO") -> logging.Logger:
    """Entrypoints call this; libraries never configure logging themselves."""
    logging.basicConfig(level=level.upper(), format=_FORMAT, datefmt="%H:%M:%S")
    logging.getLogger("aiokafka").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    return logging.getLogger(service)
