"""Database initialization for Procler using sqler."""

import logging
from pathlib import Path

from sqler import SQLerDB

from .models import LogEntry, Process, Snippet
from .settings import get_db_path

logger = logging.getLogger(__name__)

# Global database instance
_db: SQLerDB | None = None

# Current schema version - increment when making breaking changes
SCHEMA_VERSION = 1


def _get_schema_version(db: SQLerDB) -> int:
    """Get the current schema version from database metadata."""
    try:
        result = db.execute_sql(
            "SELECT value FROM procler_meta WHERE key = 'schema_version'"
        )
        if result and len(result) > 0:
            return int(result[0].get("value", 0))
        return 0
    except Exception:
        # Table doesn't exist yet
        return 0


def _set_schema_version(db: SQLerDB, version: int) -> None:
    """Set the schema version in database metadata."""
    db.execute_sql("""
        CREATE TABLE IF NOT EXISTS procler_meta (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    db.execute_sql(
        f"INSERT OR REPLACE INTO procler_meta (key, value) VALUES ('schema_version', '{version}')"
    )


def _run_migrations(db: SQLerDB, from_version: int, to_version: int) -> None:
    """Run any necessary migrations between versions."""
    # Future migrations would go here
    # Example:
    # if from_version < 2 and to_version >= 2:
    #     db._conn.execute("ALTER TABLE processes ADD COLUMN new_field TEXT")
    pass


def init_database(db_path: Path | None = None) -> SQLerDB:
    """Initialize the database and register models."""
    global _db

    if _db is not None:
        return _db

    path = db_path or get_db_path()
    _db = SQLerDB.on_disk(str(path))

    # Check and update schema version
    current_version = _get_schema_version(_db)
    if current_version < SCHEMA_VERSION:
        logger.info(f"Upgrading database schema from v{current_version} to v{SCHEMA_VERSION}")
        _run_migrations(_db, current_version, SCHEMA_VERSION)
        _set_schema_version(_db, SCHEMA_VERSION)
    elif current_version > SCHEMA_VERSION:
        logger.warning(
            f"Database schema v{current_version} is newer than app v{SCHEMA_VERSION}. "
            "Some features may not work correctly."
        )

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
