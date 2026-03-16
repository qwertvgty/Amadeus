"""SQLite storage operations."""

import sqlite3
from pathlib import Path

from loguru import logger

DB_PATH = Path("data/lifeos.db")


def get_connection() -> sqlite3.Connection:
    """Get a SQLite connection with row factory."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def ensure_db_exists() -> None:
    """Create the database if it doesn't exist by running init script."""
    if not DB_PATH.exists():
        logger.warning("Database not found, initializing...")
        from scripts.init_db import init_database

        init_database()
