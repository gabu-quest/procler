"""Abstract base class for execution contexts."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass


@dataclass
class ProcessHandle:
    """Handle to a running process."""

    pid: int
    context_type: str


@dataclass
class ExecResult:
    """Result of executing a command."""

    exit_code: int
    stdout: str
    stderr: str


class ExecutionContext(ABC):
    """Abstract base for process execution contexts (local, docker, etc.)."""

    @property
    @abstractmethod
    def context_type(self) -> str:
        """Return the context type identifier (e.g., 'local', 'docker')."""
        ...

    @abstractmethod
    async def start_process(
        self,
        command: str,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
        on_stdout: Callable[[str], None] | None = None,
        on_stderr: Callable[[str], None] | None = None,
        on_exit: Callable[[int], None] | None = None,
    ) -> ProcessHandle:
        """
        Start a long-running process.

        Args:
            command: The command to execute
            cwd: Working directory (optional)
            env: Environment variables to add (optional)
            on_stdout: Callback for stdout lines
            on_stderr: Callback for stderr lines
            on_exit: Callback when process exits with exit code

        Returns:
            ProcessHandle with the PID
        """
        ...

    @abstractmethod
    async def stop_process(self, handle: ProcessHandle, timeout: float = 10.0) -> int:
        """
        Stop a running process.

        Args:
            handle: The process handle from start_process
            timeout: Seconds to wait for graceful shutdown before SIGKILL

        Returns:
            Exit code of the process
        """
        ...

    @abstractmethod
    async def is_running(self, handle: ProcessHandle) -> bool:
        """Check if a process is still running."""
        ...

    @abstractmethod
    async def exec_command(
        self,
        command: str,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> ExecResult:
        """
        Execute a one-shot command and wait for completion.

        Args:
            command: The command to execute
            cwd: Working directory (optional)
            env: Environment variables (optional)
            timeout: Maximum execution time in seconds

        Returns:
            ExecResult with exit code, stdout, and stderr
        """
        ...

    @abstractmethod
    async def stream_logs(
        self,
        handle: ProcessHandle,
        follow: bool = True,
    ) -> AsyncIterator[tuple[str, str]]:
        """
        Stream logs from a running process.

        Args:
            handle: The process handle
            follow: If True, keep streaming as new logs arrive

        Yields:
            Tuples of (stream_type, line) where stream_type is 'stdout' or 'stderr'
        """
        ...
