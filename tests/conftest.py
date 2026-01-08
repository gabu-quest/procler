"""Pytest configuration and fixtures."""

import tempfile
from pathlib import Path

import pytest

from procgler import db
from procgler.core import context_local, process_manager


@pytest.fixture(autouse=True)
def reset_state(tmp_path):
    """Reset the database and singletons between tests."""
    # Reset singletons
    db.reset_database()
    process_manager._manager = None
    context_local._local_context = None

    # Use a temporary database for this test
    db_path = tmp_path / "test.db"
    db.init_database(db_path)

    yield

    # Clean up after test
    db.reset_database()
    process_manager._manager = None
    context_local._local_context = None


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary database for testing."""
    db_path = tmp_path / "test.db"
    database = db.init_database(db_path)
    yield database
    db.reset_database()
