"""Data models for Procgler."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


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


@dataclass
class ProcessDefinition:
    """Definition of a managed process."""

    id: int
    name: str
    command: str
    context_type: ContextType = ContextType.LOCAL
    display_name: Optional[str] = None
    container_name: Optional[str] = None
    cwd: Optional[str] = None
    env: dict[str, str] = field(default_factory=dict)
    auto_restart: bool = False
    restart_delay_seconds: int = 5
    tags: list[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class ProcessState:
    """Runtime state of a process."""

    process_id: int
    status: ProcessStatus = ProcessStatus.STOPPED
    pid: Optional[int] = None
    started_at: Optional[datetime] = None
    exit_code: Optional[int] = None
    error_message: Optional[str] = None


@dataclass
class ProcessInfo:
    """Combined process definition and state."""

    definition: ProcessDefinition
    state: ProcessState

    @property
    def name(self) -> str:
        return self.definition.name

    @property
    def status(self) -> ProcessStatus:
        return self.state.status

    @property
    def pid(self) -> Optional[int]:
        return self.state.pid

    @property
    def uptime_seconds(self) -> Optional[int]:
        if self.state.started_at and self.state.status == ProcessStatus.RUNNING:
            return int((datetime.now() - self.state.started_at).total_seconds())
        return None


@dataclass
class LogEntry:
    """A single log entry."""

    id: int
    process_id: int
    timestamp: datetime
    stream: LogStream
    line: str


@dataclass
class Snippet:
    """A saved command snippet."""

    id: int
    name: str
    command: str
    description: Optional[str] = None
    context_type: ContextType = ContextType.LOCAL
    container_name: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    created_at: Optional[datetime] = None


# JSON response envelope types


@dataclass
class SuccessResponse:
    """Successful JSON response."""

    success: bool = True
    data: Optional[dict] = None


@dataclass
class ErrorResponse:
    """Error JSON response."""

    success: bool = False
    error: str = ""
    error_code: Optional[str] = None
    suggestion: Optional[str] = None
