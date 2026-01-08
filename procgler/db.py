"""Database initialization for Procgler using sqler."""

from pathlib import Path

from sqler import SQLerDB

from .config import get_db_path
from .models import LogEntry, Process, Snippet

# Global database instance
_db: SQLerDB | None = None


def init_database(db_path: Path | None = None) -> SQLerDB:
    """Initialize the database and register models."""
    global _db

    if _db is not None:
        return _db

    path = db_path or get_db_path()
    _db = SQLerDB.on_disk(str(path))

    # Register models with the database
    Process.set_db(_db)
    LogEntry.set_db(_db)
    Snippet.set_db(_db)

    return _db


def get_database() -> SQLerDB:
    """Get the global database instance, initializing if needed."""
    if _db is None:
        return init_database()
    return _db


def reset_database() -> None:
    """Reset the global database instance (useful for testing)."""
    global _db
    _db = None
