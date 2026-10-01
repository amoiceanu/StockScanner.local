"""Application logging with rotating files and secret-safe messages."""
import logging
import time
from logging.handlers import RotatingFileHandler

from app.config import settings


def configure_logging() -> None:
    root = logging.getLogger()
    if getattr(root, "_trading_configured", False):
        return
    root.setLevel(settings.log_level)
    formatter = logging.Formatter("%(asctime)sZ %(levelname)s %(name)s %(message)s")
    formatter.converter = time.gmtime
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    app_file = RotatingFileHandler(settings.logs_dir / "app.log", maxBytes=5_000_000, backupCount=3, encoding="utf-8")
    app_file.setFormatter(formatter)
    error_file = RotatingFileHandler(settings.logs_dir / "errors.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8")
    error_file.setLevel(logging.ERROR)
    error_file.setFormatter(formatter)
    root.addHandler(console)
    root.addHandler(app_file)
    root.addHandler(error_file)
    root._trading_configured = True  # type: ignore[attr-defined]
