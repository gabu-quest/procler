"""Data models for Procler using sqler."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from sqler import SQLerModel


class ProcessStatus(str, Enum):
    """Status of a managed process."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class ContextType(str, Enum):
    """Execution context type."""

    LOCAL = "local"
    DOCKER = "docker"


class LogStream(str, Enum):
    """Log stream type."""

    STDOUT = "stdout"
    STDERR = "stderr"


# SQLer Models for database persistence


class Process(SQLerModel):
    """Process definition stored in database."""

    name: str
    command: str
    context_type: str = "local"
    display_name: str | None = None
    container_name: str | None = None
    cwd: str | None = None
    env: dict[str, str] | None = None
    auto_restart: bool = False
    restart_delay_seconds: int = 5
    tags: list[str] | None = None
    created_at: str | None = None
    updated_at: str | None = None

    # Daemon mode configuration
    daemon_mode: bool = False
    daemon_match_pattern: str | None = None
    daemon_pidfile: str | None = None
    daemon_container: str | None = None  # Container for daemon detection
    adopt_existing: bool = False

    # Log file for capturing output (used when process started via CLI or adopted)
    log_file: str | None = None  # Default: /tmp/procler/{name}.log

    # Runtime state (stored with the process)
    status: str = "stopped"
    pid: int | None = None
    started_at: str | None = None
    exit_code: int | None = None
    error_message: str | None = None
    adopted: bool = False  # Was this process adopted from an existing daemon?

    def get_context_type(self) -> ContextType:
        return ContextType(self.context_type)

    def get_status(self) -> ProcessStatus:
        return ProcessStatus(self.status)

    @property
    def uptime_seconds(self) -> int | None:
        if self.started_at and self.status == ProcessStatus.RUNNING.value:
            started = datetime.fromisoformat(self.started_at)
            return int((datetime.now() - started).total_seconds())
        return None


class LogEntry(SQLerModel):
    """Log entry stored in database."""

    process_id: int
    stream: str = "stdout"
    line: str = ""
    timestamp: str | None = None

    def get_stream(self) -> LogStream:
        return LogStream(self.stream)


class Snippet(SQLerModel):
    """Command snippet stored in database."""

    name: str
    command: str
    description: str | None = None
    context_type: str = "local"
    container_name: str | None = None
    tags: list[str] | None = None
    created_at: str | None = None

    def get_context_type(self) -> ContextType:
        return ContextType(self.context_type)


# JSON response envelope types (not stored in DB)


@dataclass
class SuccessResponse:
    """Successful JSON response."""

    success: bool = True
    data: dict | None = None


@dataclass
class ErrorResponse:
    """Error JSON response."""

    success: bool = False
    error: str = ""
    error_code: str | None = None
    suggestion: str | None = None
