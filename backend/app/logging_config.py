"""Centralized logging configuration for the application.

Call configure_logging() once at process startup (see app.main) before any
other application module logs. Log level is controlled via the LOG_LEVEL
environment variable (defaults to INFO, or DEBUG when ENV=dev).
"""

import logging
import os
import sys


def configure_logging() -> None:
    """Configure the root logger with a consistent format across the app."""
    default_level = "DEBUG" if os.getenv("ENV") == "dev" else "INFO"
    level_name = os.getenv("LOG_LEVEL", default_level).upper()
    level = getattr(logging, level_name, logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Avoid duplicate handlers if configure_logging() is called more than once
    # (e.g. under a reloader that re-imports app.main).
    if root_logger.handlers:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    root_logger.addHandler(handler)

    # Quiet down noisy third-party loggers unless we're debugging.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING if level > logging.DEBUG else logging.DEBUG)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING if level > logging.DEBUG else logging.INFO)

    logging.getLogger(__name__).info("Logging configured at level %s", level_name)
