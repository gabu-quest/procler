"""Core business logic for Procgler."""

from .context_base import ExecResult, ExecutionContext, ProcessHandle
from .context_docker import DockerContext, get_docker_context, is_docker_available
from .context_local import LocalContext, get_local_context
from .events import (
    EVENT_LOG_ENTRY,
    EVENT_STATUS_CHANGE,
    EventBus,
    get_event_bus,
    reset_event_bus,
)
from .process_manager import ProcessManager, get_process_manager
from .snippets import SnippetManager, get_snippet_manager

__all__ = [
    "ExecResult",
    "ExecutionContext",
    "ProcessHandle",
    "DockerContext",
    "get_docker_context",
    "is_docker_available",
    "LocalContext",
    "get_local_context",
    "EVENT_LOG_ENTRY",
    "EVENT_STATUS_CHANGE",
    "EventBus",
    "get_event_bus",
    "reset_event_bus",
    "ProcessManager",
    "get_process_manager",
    "SnippetManager",
    "get_snippet_manager",
]
