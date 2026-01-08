"""Configuration and settings for Procgler."""

import os
from pathlib import Path

# Default paths
DEFAULT_DATA_DIR = Path(os.environ.get("PROCGLER_DATA_DIR", Path.home() / ".procler"))
DEFAULT_DB_PATH = DEFAULT_DATA_DIR / "procler.db"

# Server defaults
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000

# Process defaults
DEFAULT_RESTART_DELAY_SECONDS = 5
DEFAULT_LOG_TAIL_LINES = 100
DEFAULT_LOG_RETENTION_LINES = 10000


def get_data_dir() -> Path:
    """Get the data directory, creating it if necessary."""
    data_dir = Path(os.environ.get("PROCGLER_DATA_DIR", DEFAULT_DATA_DIR))
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_db_path() -> Path:
    """Get the database file path."""
    return Path(os.environ.get("PROCGLER_DB_PATH", get_data_dir() / "procler.db"))
