"""Database layer for Procgler using SQLite."""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Generator, Optional

from .config import get_db_path
from .models import (
    ContextType,
    LogEntry,
    LogStream,
    ProcessDefinition,
    ProcessState,
    ProcessStatus,
    Snippet,
)

# SQL schema
SCHEMA = """
CREATE TABLE IF NOT EXISTS processes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    display_name TEXT,
    command TEXT NOT NULL,
    context_type TEXT DEFAULT 'local',
    container_name TEXT,
    cwd TEXT,
    env_json TEXT,
    auto_restart INTEGER DEFAULT 0,
    restart_delay_seconds INTEGER DEFAULT 5,
    tags_json TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS process_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    process_id INTEGER UNIQUE NOT NULL,
    status TEXT DEFAULT 'stopped',
    pid INTEGER,
    started_at TEXT,
    exit_code INTEGER,
    error_message TEXT,
    FOREIGN KEY (process_id) REFERENCES processes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    process_id INTEGER NOT NULL,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    stream TEXT DEFAULT 'stdout',
    line TEXT,
    FOREIGN KEY (process_id) REFERENCES processes(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_logs_process_timestamp ON logs(process_id, timestamp DESC);

CREATE TABLE IF NOT EXISTS snippets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    command TEXT NOT NULL,
    description TEXT,
    context_type TEXT DEFAULT 'local',
    container_name TEXT,
    tags_json TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


class Database:
    """SQLite database wrapper for Procgler."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or get_db_path()
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        """Create tables if they don't exist."""
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    @contextmanager
    def _connect(self) -> Generator[sqlite3.Connection, None, None]:
        """Get a database connection."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # Process operations

    def create_process(self, process: ProcessDefinition) -> ProcessDefinition:
        """Create a new process definition."""
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO processes (
                    name, display_name, command, context_type, container_name,
                    cwd, env_json, auto_restart, restart_delay_seconds, tags_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    process.name,
                    process.display_name,
                    process.command,
                    process.context_type.value,
                    process.container_name,
                    process.cwd,
                    json.dumps(process.env) if process.env else None,
                    int(process.auto_restart),
                    process.restart_delay_seconds,
                    json.dumps(process.tags) if process.tags else None,
                ),
            )
            process_id = cursor.lastrowid

            # Create initial state
            conn.execute(
                "INSERT INTO process_state (process_id, status) VALUES (?, ?)",
                (process_id, ProcessStatus.STOPPED.value),
            )

            # Query the created process within the same transaction
            row = conn.execute(
                "SELECT * FROM processes WHERE id = ?", (process_id,)
            ).fetchone()
            return self._row_to_process(row)

    def get_process_by_id(self, process_id: int) -> Optional[ProcessDefinition]:
        """Get a process by ID."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM processes WHERE id = ?", (process_id,)
            ).fetchone()
            return self._row_to_process(row) if row else None

    def get_process_by_name(self, name: str) -> Optional[ProcessDefinition]:
        """Get a process by name."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM processes WHERE name = ?", (name,)
            ).fetchone()
            return self._row_to_process(row) if row else None

    def list_processes(self) -> list[ProcessDefinition]:
        """List all process definitions."""
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM processes ORDER BY name").fetchall()
            return [self._row_to_process(row) for row in rows]

    def update_process(self, process: ProcessDefinition) -> ProcessDefinition:
        """Update a process definition."""
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE processes SET
                    display_name = ?, command = ?, context_type = ?,
                    container_name = ?, cwd = ?, env_json = ?,
                    auto_restart = ?, restart_delay_seconds = ?, tags_json = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    process.display_name,
                    process.command,
                    process.context_type.value,
                    process.container_name,
                    process.cwd,
                    json.dumps(process.env) if process.env else None,
                    int(process.auto_restart),
                    process.restart_delay_seconds,
                    json.dumps(process.tags) if process.tags else None,
                    process.id,
                ),
            )
            return self.get_process_by_id(process.id)

    def delete_process(self, name: str) -> bool:
        """Delete a process by name."""
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM processes WHERE name = ?", (name,))
            return cursor.rowcount > 0

    def _row_to_process(self, row: sqlite3.Row) -> ProcessDefinition:
        """Convert a database row to ProcessDefinition."""
        return ProcessDefinition(
            id=row["id"],
            name=row["name"],
            display_name=row["display_name"],
            command=row["command"],
            context_type=ContextType(row["context_type"]),
            container_name=row["container_name"],
            cwd=row["cwd"],
            env=json.loads(row["env_json"]) if row["env_json"] else {},
            auto_restart=bool(row["auto_restart"]),
            restart_delay_seconds=row["restart_delay_seconds"],
            tags=json.loads(row["tags_json"]) if row["tags_json"] else [],
            created_at=_parse_timestamp(row["created_at"]),
            updated_at=_parse_timestamp(row["updated_at"]),
        )

    # Process state operations

    def get_process_state(self, process_id: int) -> Optional[ProcessState]:
        """Get the current state of a process."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM process_state WHERE process_id = ?", (process_id,)
            ).fetchone()
            return self._row_to_state(row) if row else None

    def update_process_state(self, state: ProcessState) -> None:
        """Update process state."""
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE process_state SET
                    status = ?, pid = ?, started_at = ?,
                    exit_code = ?, error_message = ?
                WHERE process_id = ?
                """,
                (
                    state.status.value,
                    state.pid,
                    state.started_at.isoformat() if state.started_at else None,
                    state.exit_code,
                    state.error_message,
                    state.process_id,
                ),
            )

    def _row_to_state(self, row: sqlite3.Row) -> ProcessState:
        """Convert a database row to ProcessState."""
        return ProcessState(
            process_id=row["process_id"],
            status=ProcessStatus(row["status"]),
            pid=row["pid"],
            started_at=_parse_timestamp(row["started_at"]),
            exit_code=row["exit_code"],
            error_message=row["error_message"],
        )

    # Log operations

    def add_log(self, process_id: int, line: str, stream: LogStream = LogStream.STDOUT) -> None:
        """Add a log entry."""
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO logs (process_id, stream, line) VALUES (?, ?, ?)",
                (process_id, stream.value, line),
            )

    def get_logs(
        self,
        process_id: int,
        tail: int = 100,
        since: Optional[datetime] = None,
    ) -> list[LogEntry]:
        """Get logs for a process."""
        with self._connect() as conn:
            if since:
                rows = conn.execute(
                    """
                    SELECT * FROM logs
                    WHERE process_id = ? AND timestamp >= ?
                    ORDER BY timestamp DESC LIMIT ?
                    """,
                    (process_id, since.isoformat(), tail),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT * FROM logs
                    WHERE process_id = ?
                    ORDER BY timestamp DESC LIMIT ?
                    """,
                    (process_id, tail),
                ).fetchall()

            return [self._row_to_log(row) for row in reversed(rows)]

    def cleanup_logs(self, process_id: int, keep_lines: int = 10000) -> int:
        """Delete old logs, keeping only the most recent entries."""
        with self._connect() as conn:
            cursor = conn.execute(
                """
                DELETE FROM logs WHERE id IN (
                    SELECT id FROM logs
                    WHERE process_id = ?
                    ORDER BY timestamp DESC
                    LIMIT -1 OFFSET ?
                )
                """,
                (process_id, keep_lines),
            )
            return cursor.rowcount

    def _row_to_log(self, row: sqlite3.Row) -> LogEntry:
        """Convert a database row to LogEntry."""
        return LogEntry(
            id=row["id"],
            process_id=row["process_id"],
            timestamp=_parse_timestamp(row["timestamp"]),
            stream=LogStream(row["stream"]),
            line=row["line"],
        )

    # Snippet operations

    def create_snippet(self, snippet: Snippet) -> Snippet:
        """Create a new snippet."""
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO snippets (
                    name, command, description, context_type, container_name, tags_json
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    snippet.name,
                    snippet.command,
                    snippet.description,
                    snippet.context_type.value,
                    snippet.container_name,
                    json.dumps(snippet.tags) if snippet.tags else None,
                ),
            )
            return self.get_snippet_by_id(cursor.lastrowid)

    def get_snippet_by_id(self, snippet_id: int) -> Optional[Snippet]:
        """Get a snippet by ID."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM snippets WHERE id = ?", (snippet_id,)
            ).fetchone()
            return self._row_to_snippet(row) if row else None

    def get_snippet_by_name(self, name: str) -> Optional[Snippet]:
        """Get a snippet by name."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM snippets WHERE name = ?", (name,)
            ).fetchone()
            return self._row_to_snippet(row) if row else None

    def list_snippets(self, tag: Optional[str] = None) -> list[Snippet]:
        """List all snippets, optionally filtered by tag."""
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM snippets ORDER BY name").fetchall()
            snippets = [self._row_to_snippet(row) for row in rows]
            if tag:
                snippets = [s for s in snippets if tag in s.tags]
            return snippets

    def delete_snippet(self, name: str) -> bool:
        """Delete a snippet by name."""
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM snippets WHERE name = ?", (name,))
            return cursor.rowcount > 0

    def _row_to_snippet(self, row: sqlite3.Row) -> Snippet:
        """Convert a database row to Snippet."""
        return Snippet(
            id=row["id"],
            name=row["name"],
            command=row["command"],
            description=row["description"],
            context_type=ContextType(row["context_type"]),
            container_name=row["container_name"],
            tags=json.loads(row["tags_json"]) if row["tags_json"] else [],
            created_at=_parse_timestamp(row["created_at"]),
        )


def _parse_timestamp(value: Optional[str]) -> Optional[datetime]:
    """Parse an ISO timestamp string."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


# Global database instance
_db: Optional[Database] = None


def get_database() -> Database:
    """Get the global database instance."""
    global _db
    if _db is None:
        _db = Database()
    return _db
