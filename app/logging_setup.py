"""Logging sozlamasi — butun ilova uchun yagona format."""
import logging
import sys

_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"


def setup_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    if root.handlers:
        root.setLevel(level.upper())
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_FORMAT))
    root.addHandler(handler)
    root.setLevel(level.upper())
    # Shovqinli kutubxonalarni pasaytiramiz; httpx URL ichida kalit chiqmasin.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("aiogram.event").setLevel(logging.WARNING)
