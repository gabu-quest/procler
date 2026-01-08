"""Pytest configuration and fixtures."""

import tempfile
from pathlib import Path

import pytest

from procler import db
from procler.core import context_local, events, process_manager, snippets, groups, recipes
from procler.config import loader as config_loader


@pytest.fixture(autouse=True)
def reset_state(tmp_path):
    """Reset the database and singletons between tests."""
    # Reset singletons
    db.reset_database()
    process_manager._manager = None
    context_local._local_context = None
    snippets._snippet_manager = None
    groups._group_manager = None
    recipes._recipe_executor = None
    events.reset_event_bus()
    config_loader.reset_config_cache()

    # Use a temporary database for this test
    db_path = tmp_path / "test.db"
    db.init_database(db_path)

    yield

    # Clean up after test
    db.reset_database()
    process_manager._manager = None
    context_local._local_context = None
    snippets._snippet_manager = None
    groups._group_manager = None
    recipes._recipe_executor = None
    events.reset_event_bus()
    config_loader.reset_config_cache()


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary database for testing."""
    db_path = tmp_path / "test.db"
    database = db.init_database(db_path)
    yield database
    db.reset_database()
