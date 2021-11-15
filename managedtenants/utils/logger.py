import logging
import sys


def get_text_logger(name, level=logging.INFO):
    """Returns a singleton text logger, with name and level."""
    return TextLoggersSingleton(name, level)


def setup_text_logger(name, level):
    res = logging.getLogger(name)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt="%(message)s"))
    res.addHandler(handler)
    res.setLevel(level)
    return res


class TextLoggersSingleton:
    """Singleton wrapper around text loggers."""

    _instances = {}

    def __new__(cls, name, level):
        if cls._instances.get(name) is None:
            cls._instances[name] = setup_text_logger(name, level)
        return cls._instances[name]
