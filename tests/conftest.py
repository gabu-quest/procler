"""Pytest configuration and fixtures."""

import pytest

from procler import db
from procler.config import loader as config_loader
from procler.core import context_local, events, groups, health, process_manager, recipes, snippets


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
    health.reset_health_checker()
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
    health.reset_health_checker()
    events.reset_event_bus()
    config_loader.reset_config_cache()


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary database for testing."""
    db_path = tmp_path / "test.db"
    database = db.init_database(db_path)
    yield database
    db.reset_database()
