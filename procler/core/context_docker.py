"""Docker container execution context using docker-py SDK."""

import asyncio
from collections.abc import AsyncIterator, Callable

try:
    import docker
    from docker.errors import APIError, NotFound

    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False

from .context_base import ExecResult, ExecutionContext, ProcessHandle


class DockerContext(ExecutionContext):
    """Execute processes inside Docker containers using docker-py SDK."""

    def __init__(self):
        if not DOCKER_AVAILABLE:
            raise RuntimeError("Docker SDK not available. Install with: pip install docker")
        self._client = docker.from_env()
        self._exec_instances: dict[int, tuple] = {}  # pid -> (container, exec_id)

    @property
    def context_type(self) -> str:
        return "docker"

    def _get_container(self, container_name: str):
        """Get a container by name or ID."""
        try:
            return self._client.containers.get(container_name)
        except NotFound:
            raise ValueError(f"Container '{container_name}' not found")

    def _is_container_running(self, container_name: str) -> bool:
        """Check if a container is running."""
        try:
            container = self._get_container(container_name)
            return container.status == "running"
        except ValueError:
            return False

    def list_containers(self, running_only: bool = True) -> list[dict]:
        """List available containers."""
        containers = self._client.containers.list(all=not running_only)
        return [
            {
                "id": c.short_id,
                "name": c.name,
                "status": c.status,
                "image": c.image.tags[0] if c.image.tags else c.image.short_id,
            }
            for c in containers
        ]

    async def start_process(
        self,
        command: str,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
        on_stdout: Callable[[str], None] | None = None,
        on_stderr: Callable[[str], None] | None = None,
        on_exit: Callable[[int], None] | None = None,
        container_name: str | None = None,
    ) -> ProcessHandle:
        """
        Start a long-running process inside a Docker container.

        Note: Docker exec doesn't support background processes the same way
        as local subprocesses. This implementation runs the command and
        streams output, but the "PID" is actually a unique identifier
        for the exec instance, not a real container PID.
        """
        if not container_name:
            raise ValueError("container_name is required for Docker context")

        container = self._get_container(container_name)

        if container.status != "running":
            raise RuntimeError(f"Container '{container_name}' is not running (status: {container.status})")

        # Build environment variables list
        env_list = [f"{k}={v}" for k, v in (env or {}).items()]

        # Create exec instance
        exec_result = container.client.api.exec_create(
            container.id,
            command,
            workdir=cwd,
            environment=env_list if env_list else None,
            stdout=True,
            stderr=True,
            tty=False,
        )
        exec_id = exec_result["Id"]

        # Start exec and get stream handle
        try:
            output = container.client.api.exec_start(exec_id, stream=True, demux=True)
        except Exception as e:
            raise RuntimeError(f"Failed to start exec in container '{container_name}': {e}") from e

        def resolve_exec_pid() -> int:
            """Resolve the real PID for this exec session inside the container."""
            try:
                inspect = container.client.api.exec_inspect(exec_id)
                pid = inspect.get("Pid")
                if isinstance(pid, int) and pid > 0:
                    return pid
            except Exception:
                return 0
            return 0

        exec_pid = resolve_exec_pid()
        if exec_pid <= 0:
            # Wait briefly for PID to appear
            for _ in range(10):
                await asyncio.sleep(0.1)
                exec_pid = resolve_exec_pid()
                if exec_pid > 0:
                    break

        # Fall back to a pseudo pid if Docker doesn't report one
        if exec_pid <= 0:
            import random

            exec_pid = random.randint(100000, 999999)

        self._exec_instances[exec_pid] = (container, exec_id)

        # Start streaming output in background
        async def stream_output():
            try:
                for stdout_chunk, stderr_chunk in output:
                    if stdout_chunk:
                        for line in stdout_chunk.decode("utf-8", errors="replace").splitlines():
                            if on_stdout:
                                on_stdout(line)
                    if stderr_chunk:
                        for line in stderr_chunk.decode("utf-8", errors="replace").splitlines():
                            if on_stderr:
                                on_stderr(line)

                # Get exit code
                inspect = container.client.api.exec_inspect(exec_id)
                exit_code = inspect.get("ExitCode", 0)

                if on_exit:
                    on_exit(exit_code)

            except Exception as e:
                if on_stderr:
                    on_stderr(f"Error streaming output: {e}")
                if on_exit:
                    on_exit(-1)
            finally:
                if exec_pid in self._exec_instances:
                    del self._exec_instances[exec_pid]

        # Run in background
        asyncio.create_task(stream_output())

        return ProcessHandle(pid=exec_pid, context_type=self.context_type)

    async def stop_process(self, handle: ProcessHandle, timeout: float = 10.0) -> int:
        """
        Stop a running process in a Docker container.

        Note: Docker exec instances cannot be stopped directly. We can only
        wait for them to complete or kill the container (which is destructive).
        """
        if handle.pid not in self._exec_instances:
            return 0  # Already done

        container, exec_id = self._exec_instances[handle.pid]

        # Check if still running
        try:
            inspect = container.client.api.exec_inspect(exec_id)
            if not inspect.get("Running", False):
                exit_code = inspect.get("ExitCode", 0)
                del self._exec_instances[handle.pid]
                return exit_code
        except Exception:
            pass

        # Wait for completion (can't really kill exec)
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < timeout:
            await asyncio.sleep(0.1)
            try:
                inspect = container.client.api.exec_inspect(exec_id)
                if not inspect.get("Running", False):
                    exit_code = inspect.get("ExitCode", 0)
                    if handle.pid in self._exec_instances:
                        del self._exec_instances[handle.pid]
                    return exit_code
            except Exception:
                break

        # Timeout - process may still be running
        if handle.pid in self._exec_instances:
            del self._exec_instances[handle.pid]
        return -1

    async def is_running(self, handle: ProcessHandle) -> bool:
        """Check if a process is still running."""
        if handle.pid not in self._exec_instances:
            return False

        container, exec_id = self._exec_instances[handle.pid]

        try:
            inspect = container.client.api.exec_inspect(exec_id)
            return inspect.get("Running", False)
        except Exception:
            return False

    async def exec_command(
        self,
        command: str,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
        timeout: float | None = None,
        container_name: str | None = None,
    ) -> ExecResult:
        """Execute a one-shot command inside a Docker container."""
        if not container_name:
            raise ValueError("container_name is required for Docker context")

        container = self._get_container(container_name)

        if container.status != "running":
            return ExecResult(
                exit_code=-1,
                stdout="",
                stderr=f"Container '{container_name}' is not running (status: {container.status})",
            )

        # Build environment variables list
        env_list = [f"{k}={v}" for k, v in (env or {}).items()]

        try:
            # Run command with exec
            exit_code, output = container.exec_run(
                command,
                workdir=cwd,
                environment=env_list if env_list else None,
                demux=True,
            )

            stdout = ""
            stderr = ""

            if output:
                stdout_bytes, stderr_bytes = output
                if stdout_bytes:
                    stdout = stdout_bytes.decode("utf-8", errors="replace")
                if stderr_bytes:
                    stderr = stderr_bytes.decode("utf-8", errors="replace")

            return ExecResult(
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
            )

        except APIError as e:
            return ExecResult(
                exit_code=-1,
                stdout="",
                stderr=f"Docker API error: {e}",
            )
        except Exception as e:
            return ExecResult(
                exit_code=-1,
                stdout="",
                stderr=f"Error executing command: {e}",
            )

    async def stream_logs(
        self,
        handle: ProcessHandle,
        follow: bool = True,
    ) -> AsyncIterator[tuple[str, str]]:
        """
        Stream logs from a running process in a Docker container.

        Note: For Docker exec, logs are captured during exec_start.
        This method is a placeholder for compatibility.
        """
        # Docker exec logs are streamed during execution, not after
        # For container logs, use container.logs()
        return
        yield  # Make this a generator


# Global singleton for Docker context
_docker_context: DockerContext | None = None


def get_docker_context() -> DockerContext:
    """Get the global DockerContext instance."""
    global _docker_context
    if _docker_context is None:
        _docker_context = DockerContext()
    return _docker_context


def is_docker_available() -> bool:
    """Check if Docker is available."""
    if not DOCKER_AVAILABLE:
        return False
    try:
        client = docker.from_env()
        client.ping()
        return True
    except Exception:
        return False
