"""Database compatibility tests."""

import warnings
from pathlib import Path

from sqler import SQLerDB

from procler import db as procler_db
from procler.models import Process

READ_ONLY_SQL = {"SELECT", "EXPLAIN", "PRAGMA", "WITH"}


def _install_read_only_execute_sql_guard(monkeypatch) -> None:
    original_execute_sql = SQLerDB.execute_sql

    def guarded_execute_sql(self, query, params=None):
        first_word = query.strip().split()[0].upper()
        if first_word not in READ_ONLY_SQL:
            raise AssertionError(f"execute_sql used for write SQL: {first_word}")
        return original_execute_sql(self, query, params)

    monkeypatch.setattr(SQLerDB, "execute_sql", guarded_execute_sql)


def _schema_version(database: SQLerDB) -> int:
    result = database.execute_sql("SELECT value FROM procler_meta WHERE key = 'schema_version'")
    return int(result[0]["value"])


def _create_legacy_v1_database(path: Path) -> None:
    database = SQLerDB.on_disk(str(path))
    database.adapter.execute("""
        CREATE TABLE process (
            _id INTEGER PRIMARY KEY AUTOINCREMENT,
            data JSON NOT NULL
        )
    """)
    database.adapter.execute("""
        CREATE TABLE procler_meta (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    database.adapter.execute(
        "INSERT INTO procler_meta (key, value) VALUES (?, ?)",
        ["schema_version", "1"],
    )
    database.adapter.auto_commit()
    database.close()


def test_init_database_keeps_execute_sql_read_only(monkeypatch, tmp_path):
    """sqler execute_sql is read-only; procler schema writes use the adapter."""
    _install_read_only_execute_sql_guard(monkeypatch)
    procler_db.reset_database()

    database = procler_db.init_database(tmp_path / "state.db")

    assert _schema_version(database) == procler_db.SCHEMA_VERSION
    process = Process(name="api", command="echo ok")
    process.save()
    assert process._id is not None


def test_legacy_v1_migration_uses_adapter_for_alter_table(monkeypatch, tmp_path):
    """Old state DBs can migrate even when execute_sql rejects write statements."""
    _install_read_only_execute_sql_guard(monkeypatch)
    db_path = tmp_path / "legacy.db"
    _create_legacy_v1_database(db_path)
    procler_db.reset_database()

    database = procler_db.init_database(db_path)

    columns = database.execute_sql("PRAGMA table_info(process)")
    assert any(column["name"] == "namespace" for column in columns)
    assert _schema_version(database) == procler_db.SCHEMA_VERSION


def test_init_database_does_not_emit_sqler_set_db_deprecations(tmp_path):
    """sqler warns on class binding; procler keeps that internal at startup."""
    procler_db.reset_database()

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        procler_db.init_database(tmp_path / "state.db")

    set_db_warnings = [
        warning for warning in captured if "set_db() is deprecated" in str(warning.message)
    ]
    assert set_db_warnings == []
