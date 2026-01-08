"""Pytest configuration and fixtures."""

import tempfile
from pathlib import Path

import pytest

from procgler import db


@pytest.fixture(autouse=True)
def reset_db():
    """Reset the database between tests."""
    db.reset_database()
    yield
    db.reset_database()


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        database = db.init_database(db_path)
        yield database
        db.reset_database()
