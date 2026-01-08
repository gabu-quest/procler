"""Dependency injection for FastAPI routes."""

from ..core import ProcessManager, SnippetManager, get_process_manager, get_snippet_manager
from ..db import init_database


def get_db():
    """Initialize and return the database."""
    return init_database()


def get_manager() -> ProcessManager:
    """Get the ProcessManager instance."""
    init_database()
    return get_process_manager()


def get_snippets() -> SnippetManager:
    """Get the SnippetManager instance."""
    init_database()
    return get_snippet_manager()
