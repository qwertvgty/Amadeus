"""Loguru-based logging configuration."""

import sys

from loguru import logger

from backend.app.core.config import settings


def setup_logger() -> None:
    """Configure loguru logger for the application."""
    logger.remove()  # Remove default handler

    # Console output
    logger.add(
        sys.stderr,
        level=settings.log_level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
    )

    # File output
    logger.add(
        "logs/lifeos_{time:YYYY-MM-DD}.log",
        level="DEBUG",
        rotation="1 day",
        retention="7 days",
        encoding="utf-8",
    )
