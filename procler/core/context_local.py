"""Local subprocess execution context."""

import asyncio
import os
from collections.abc import AsyncIterator, Callable

from .context_base import ExecResult, ExecutionContext, ProcessHandle


class ManagedProcess:
    """Internal wrapper for a managed asyncio subprocess."""

    def __init__(
        self,
        process: asyncio.subprocess.Process,
        stdout_task: asyncio.Task | None = None,
        stderr_task: asyncio.Task | None = None,
    ):
        self.process = process
        self.stdout_task = stdout_task
        self.stderr_task = stderr_task
        self._stdout_lines: list[str] = []
        self._stderr_lines: list[str] = []

    @property
    def pid(self) -> int:
        return self.process.pid

    def is_running(self) -> bool:
        return self.process.returncode is None

    async def wait(self) -> int:
        """Wait for process to complete and return exit code."""
        return await self.process.wait()

    def terminate(self) -> None:
        """Send SIGTERM to the process."""
        if self.is_running():
            self.process.terminate()

    def kill(self) -> None:
        """Send SIGKILL to the process."""
        if self.is_running():
            self.process.kill()

    async def cancel_io_tasks(self) -> None:
        """Cancel the stdout/stderr reading tasks."""
        for task in [self.stdout_task, self.stderr_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass


class LocalContext(ExecutionContext):
    """Execute processes as local subprocesses using asyncio."""

    def __init__(self):
        self._processes: dict[int, ManagedProcess] = {}

    @property
    def context_type(self) -> str:
        return "local"

    async def start_process(
        self,
        command: str,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
        on_stdout: Callable[[str], None] | None = None,
        on_stderr: Callable[[str], None] | None = None,
        on_exit: Callable[[int], None] | None = None,
    ) -> ProcessHandle:
        """Start a long-running local subprocess."""
        # Merge environment
        process_env = os.environ.copy()
        if env:
            process_env.update(env)

        # Start the process
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=process_env,
            start_new_session=True,  # Allows killing the whole process group
        )

        managed = ManagedProcess(process)

        # Start tasks to read stdout/stderr
        if process.stdout:
            managed.stdout_task = asyncio.create_task(self._read_stream(process.stdout, "stdout", managed, on_stdout))

        if process.stderr:
            managed.stderr_task = asyncio.create_task(self._read_stream(process.stderr, "stderr", managed, on_stderr))

        # Start a task to monitor process exit
        if on_exit:
            asyncio.create_task(self._monitor_exit(managed, on_exit))

        self._processes[process.pid] = managed

        return ProcessHandle(pid=process.pid, context_type=self.context_type)

    async def _read_stream(
        self,
        stream: asyncio.StreamReader,
        stream_type: str,
        managed: ManagedProcess,
        callback: Callable[[str], None] | None,
    ) -> None:
        """Read lines from a stream and invoke callback."""
        try:
            while True:
                line = await stream.readline()
                if not line:
                    break
                decoded = line.decode("utf-8", errors="replace").rstrip("\n\r")
                if stream_type == "stdout":
                    managed._stdout_lines.append(decoded)
                else:
                    managed._stderr_lines.append(decoded)
                if callback:
                    callback(decoded)
        except asyncio.CancelledError:
            pass

    async def _monitor_exit(
        self,
        managed: ManagedProcess,
        callback: Callable[[int], None],
    ) -> None:
        """Monitor process exit and invoke callback."""
        exit_code = await managed.wait()
        callback(exit_code)

    async def stop_process(self, handle: ProcessHandle, timeout: float = 10.0) -> int:
        """Stop a running process gracefully, then forcefully if needed."""
        managed = self._processes.get(handle.pid)
        if not managed:
            return -1

        if not managed.is_running():
            exit_code = managed.process.returncode or 0
            await managed.cancel_io_tasks()
            del self._processes[handle.pid]
            return exit_code

        # Try graceful termination first
        managed.terminate()

        try:
            exit_code = await asyncio.wait_for(managed.wait(), timeout=timeout)
        except TimeoutError:
            # Force kill if graceful shutdown times out
            managed.kill()
            exit_code = await managed.wait()

        await managed.cancel_io_tasks()
        del self._processes[handle.pid]

        return exit_code

    async def is_running(self, handle: ProcessHandle) -> bool:
        """Check if a process is still running."""
        managed = self._processes.get(handle.pid)
        if not managed:
            return False
        return managed.is_running()

    async def exec_command(
        self,
        command: str,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> ExecResult:
        """Execute a one-shot command and wait for completion."""
        process_env = os.environ.copy()
        if env:
            process_env.update(env)

        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=process_env,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )
        except TimeoutError:
            process.kill()
            await process.wait()
            return ExecResult(
                exit_code=-1,
                stdout="",
                stderr=f"Command timed out after {timeout} seconds",
            )

        return ExecResult(
            exit_code=process.returncode or 0,
            stdout=stdout.decode("utf-8", errors="replace"),
            stderr=stderr.decode("utf-8", errors="replace"),
        )

    async def stream_logs(
        self,
        handle: ProcessHandle,
        follow: bool = True,
    ) -> AsyncIterator[tuple[str, str]]:
        """Stream logs from a running process."""
        managed = self._processes.get(handle.pid)
        if not managed:
            return

        # First yield any buffered lines
        for line in managed._stdout_lines:
            yield ("stdout", line)
        for line in managed._stderr_lines:
            yield ("stderr", line)

        if not follow:
            return

        # For follow mode, we'd need a more sophisticated approach
        # with queues. For now, just poll the buffer.
        last_stdout_idx = len(managed._stdout_lines)
        last_stderr_idx = len(managed._stderr_lines)

        while managed.is_running():
            await asyncio.sleep(0.1)

            # Check for new stdout lines
            while last_stdout_idx < len(managed._stdout_lines):
                yield ("stdout", managed._stdout_lines[last_stdout_idx])
                last_stdout_idx += 1

            # Check for new stderr lines
            while last_stderr_idx < len(managed._stderr_lines):
                yield ("stderr", managed._stderr_lines[last_stderr_idx])
                last_stderr_idx += 1

    def get_managed_process(self, pid: int) -> ManagedProcess | None:
        """Get a managed process by PID (for internal use)."""
        return self._processes.get(pid)


# Global singleton for the local context
_local_context: LocalContext | None = None


def get_local_context() -> LocalContext:
    """Get the global LocalContext instance."""
    global _local_context
    if _local_context is None:
        _local_context = LocalContext()
    return _local_context
