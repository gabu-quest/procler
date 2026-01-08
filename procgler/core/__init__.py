"""Core business logic for Procgler."""

from .context_base import ExecResult, ExecutionContext, ProcessHandle
from .context_docker import DockerContext, get_docker_context, is_docker_available
from .context_local import LocalContext, get_local_context
from .process_manager import ProcessManager, get_process_manager

__all__ = [
    "ExecResult",
    "ExecutionContext",
    "ProcessHandle",
    "DockerContext",
    "get_docker_context",
    "is_docker_available",
    "LocalContext",
    "get_local_context",
    "ProcessManager",
    "get_process_manager",
]
