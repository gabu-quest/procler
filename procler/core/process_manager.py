"""Central process manager coordinating all process operations."""

import asyncio
from datetime import datetime, timedelta
from typing import Any

from sqler.query import SQLerField as F

from ..db import init_database
from ..models import LogEntry, Process, ProcessStatus
from .context_base import ExecResult, ExecutionContext, ProcessHandle
from .context_docker import get_docker_context, is_docker_available
from .context_local import LocalContext, get_local_context
from .events import EVENT_LOG_ENTRY, EVENT_STATUS_CHANGE, get_event_bus

# Default max log entries per process
DEFAULT_MAX_LOGS = 10000


def parse_duration(duration: str) -> int:
    """Parse a duration string like '5m', '1h', '30s' to seconds."""
    if not duration:
        return 0

    duration = duration.strip().lower()

    # Try ISO timestamp first
    try:
        dt = datetime.fromisoformat(duration)
        return int((datetime.now() - dt).total_seconds())
    except ValueError:
        pass

    multipliers = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400,
    }

    if duration[-1] in multipliers:
        try:
            value = int(duration[:-1])
            return value * multipliers[duration[-1]]
        except ValueError:
            pass

    # Try as raw seconds
    try:
        return int(duration)
    except ValueError:
        raise ValueError(f"Invalid duration format: {duration}")


class ProcessManager:
    """Central coordinator for process operations."""

    def __init__(self):
        self._contexts: dict[str, ExecutionContext] = {}
        self._handles: dict[int, ProcessHandle] = {}  # process_id -> handle
        self._init_contexts()

    def _init_contexts(self) -> None:
        """Initialize execution contexts."""
        self._contexts["local"] = get_local_context()
        # Add Docker context if available
        if is_docker_available():
            try:
                self._contexts["docker"] = get_docker_context()
            except Exception:
                pass  # Docker not available or not running

    def _get_context(self, context_type: str) -> ExecutionContext:
        """Get the execution context for a given type."""
        context = self._contexts.get(context_type)
        if not context:
            raise ValueError(f"Unknown context type: {context_type}")
        return context

    def _get_process_by_name(self, name: str) -> Process | None:
        """Get a process by name."""
        results = Process.query().filter(F("name") == name).all()
        return results[0] if results else None

    def _log_callback(self, process_id: int, stream: str):
        """Create a callback for logging output."""
        def callback(line: str) -> None:
            timestamp = datetime.now().isoformat()
            entry = LogEntry(
                process_id=process_id,
                stream=stream,
                line=line,
                timestamp=timestamp,
            )
            entry.save()

            # Emit event for WebSocket broadcast
            get_event_bus().emit_sync(
                EVENT_LOG_ENTRY,
                {
                    "process_id": process_id,
                    "stream": stream,
                    "line": line,
                    "timestamp": timestamp,
                },
            )
        return callback

    def _exit_callback(self, process: Process):
        """Create a callback for process exit."""
        def callback(exit_code: int) -> None:
            # Reload process to get latest state
            updated = Process.from_id(process._id)
            if updated:
                updated.status = ProcessStatus.STOPPED.value
                updated.exit_code = exit_code
                updated.pid = None
                updated.save()
                # Remove handle
                if process._id in self._handles:
                    del self._handles[process._id]

                # Emit status change event
                get_event_bus().emit_sync(
                    EVENT_STATUS_CHANGE,
                    {
                        "process_id": process._id,
                        "name": updated.name,
                        "status": updated.status,
                        "exit_code": exit_code,
                        "pid": None,
                    },
                )
        return callback

    async def start(self, name: str) -> dict[str, Any]:
        """
        Start a process by name.

        Returns a dict with status and process info (for JSON output).
        """
        init_database()
        process = self._get_process_by_name(name)

        if not process:
            return {
                "success": False,
                "error": f"Process '{name}' not found",
                "error_code": "process_not_found",
            }

        # Check if already running
        if process.status == ProcessStatus.RUNNING.value:
            is_running = False
            handle = self._handles.get(process._id)
            if handle:
                context = self._get_context(process.context_type)
                is_running = await context.is_running(handle)
            elif process.pid:
                # No handle but we have a PID - check OS directly
                is_running = self._is_pid_running(process.pid)

            if is_running:
                return {
                    "success": True,
                    "data": {
                        "status": "already_running",
                        "process": self._process_to_dict(process),
                    },
                }

        # Get the appropriate context
        try:
            context = self._get_context(process.context_type)
        except ValueError:
            if process.context_type == "docker" and not is_docker_available():
                return {
                    "success": False,
                    "error": "Docker is not available",
                    "error_code": "docker_unavailable",
                    "suggestion": "Ensure Docker is installed and running",
                }
            return {
                "success": False,
                "error": f"Unknown context type: {process.context_type}",
                "error_code": "invalid_context",
            }

        # Validate Docker context requirements
        if process.context_type == "docker" and not process.container_name:
            return {
                "success": False,
                "error": "Container name required for docker context",
                "error_code": "missing_container",
                "suggestion": "Define process with --container <name>",
            }

        # Update status to starting
        process.status = ProcessStatus.STARTING.value
        process.save()

        try:
            # Start the process (Docker context needs container_name)
            if process.context_type == "docker":
                handle = await context.start_process(
                    command=process.command,
                    cwd=process.cwd,
                    env=process.env,
                    on_stdout=self._log_callback(process._id, "stdout"),
                    on_stderr=self._log_callback(process._id, "stderr"),
                    on_exit=self._exit_callback(process),
                    container_name=process.container_name,
                )
            else:
                handle = await context.start_process(
                    command=process.command,
                    cwd=process.cwd,
                    env=process.env,
                    on_stdout=self._log_callback(process._id, "stdout"),
                    on_stderr=self._log_callback(process._id, "stderr"),
                    on_exit=self._exit_callback(process),
                )

            # Update process state
            process.status = ProcessStatus.RUNNING.value
            process.pid = handle.pid
            process.started_at = datetime.now().isoformat()
            process.exit_code = None
            process.error_message = None
            process.save()

            # Store handle
            self._handles[process._id] = handle

            # Emit status change event
            get_event_bus().emit_sync(
                EVENT_STATUS_CHANGE,
                {
                    "process_id": process._id,
                    "name": process.name,
                    "status": process.status,
                    "pid": process.pid,
                },
            )

            return {
                "success": True,
                "data": {
                    "status": "started",
                    "process": self._process_to_dict(process),
                },
            }

        except Exception as e:
            process.status = ProcessStatus.ERROR.value
            process.error_message = str(e)
            process.save()

            return {
                "success": False,
                "error": f"Failed to start process: {e}",
                "error_code": "start_failed",
            }

    async def stop(self, name: str, timeout: float = 10.0) -> dict[str, Any]:
        """
        Stop a process by name.

        Returns a dict with status and process info (for JSON output).
        """
        init_database()
        process = self._get_process_by_name(name)

        if not process:
            return {
                "success": False,
                "error": f"Process '{name}' not found",
                "error_code": "process_not_found",
            }

        # Check if already stopped
        if process.status == ProcessStatus.STOPPED.value:
            return {
                "success": True,
                "data": {
                    "status": "already_stopped",
                    "process": self._process_to_dict(process),
                },
            }

        handle = self._handles.get(process._id)

        # Update status to stopping
        process.status = ProcessStatus.STOPPING.value
        process.save()

        try:
            exit_code = 0
            if process.pid and self._is_pid_running(process.pid):
                # PID is running - kill directly (most reliable across CLI invocations)
                exit_code = await self._kill_pid(process.pid, timeout=timeout)
            elif handle:
                # Try handle-based stop (works within same event loop only)
                try:
                    context = self._get_context(process.context_type)
                    exit_code = await context.stop_process(handle, timeout=timeout)
                except RuntimeError:
                    # Handle attached to closed event loop - process likely already dead
                    pass

            # Update process state
            process.status = ProcessStatus.STOPPED.value
            process.pid = None
            process.exit_code = exit_code
            process.save()

            # Remove handle
            if process._id in self._handles:
                del self._handles[process._id]

            # Emit status change event
            get_event_bus().emit_sync(
                EVENT_STATUS_CHANGE,
                {
                    "process_id": process._id,
                    "name": process.name,
                    "status": process.status,
                    "exit_code": exit_code,
                    "pid": None,
                },
            )

            return {
                "success": True,
                "data": {
                    "status": "stopped",
                    "exit_code": exit_code,
                    "process": self._process_to_dict(process),
                },
            }

        except Exception as e:
            process.status = ProcessStatus.ERROR.value
            process.error_message = str(e)
            process.save()

            # Emit error status event
            get_event_bus().emit_sync(
                EVENT_STATUS_CHANGE,
                {
                    "process_id": process._id,
                    "name": process.name,
                    "status": process.status,
                    "error_message": str(e),
                },
            )

            return {
                "success": False,
                "error": f"Failed to stop process: {e}",
                "error_code": "stop_failed",
            }

    async def restart(self, name: str, timeout: float = 10.0) -> dict[str, Any]:
        """
        Restart a process by name (stop then start).

        Returns a dict with status and process info (for JSON output).
        """
        init_database()
        process = self._get_process_by_name(name)

        if not process:
            return {
                "success": False,
                "error": f"Process '{name}' not found",
                "error_code": "process_not_found",
            }

        # Stop if running
        if process.status in [ProcessStatus.RUNNING.value, ProcessStatus.STARTING.value]:
            stop_result = await self.stop(name, timeout=timeout)
            if not stop_result["success"]:
                return stop_result

        # Start
        return await self.start(name)

    async def status(self, name: str | None = None) -> dict[str, Any]:
        """
        Get status of one or all processes.

        Returns a dict with process info (for JSON output).
        """
        init_database()

        if name:
            process = self._get_process_by_name(name)
            if not process:
                return {
                    "success": False,
                    "error": f"Process '{name}' not found",
                    "error_code": "process_not_found",
                }

            # Verify running status
            await self._verify_running_status(process)

            return {
                "success": True,
                "data": {
                    "process": self._process_to_dict(process),
                },
            }
        else:
            processes = Process.query().all()
            for p in processes:
                await self._verify_running_status(p)

            return {
                "success": True,
                "data": {
                    "processes": [self._process_to_dict(p) for p in processes],
                },
            }

    async def _verify_running_status(self, process: Process) -> None:
        """Verify and update the running status of a process."""
        if process.status != ProcessStatus.RUNNING.value:
            return

        handle = self._handles.get(process._id)
        if handle:
            # We have a handle, check via context
            context = self._get_context(process.context_type)
            if not await context.is_running(handle):
                process.status = ProcessStatus.STOPPED.value
                process.pid = None
                process.save()
                del self._handles[process._id]
        elif process.pid:
            # No handle but we have a PID - check OS directly
            if not self._is_pid_running(process.pid):
                process.status = ProcessStatus.STOPPED.value
                process.pid = None
                process.save()
        else:
            # No handle and no PID - mark as stopped
            process.status = ProcessStatus.STOPPED.value
            process.save()

    def _is_pid_running(self, pid: int) -> bool:
        """Check if a PID is still running in the OS."""
        import os

        try:
            os.kill(pid, 0)  # Signal 0 just checks if process exists
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            # Process exists but we don't have permission to signal it
            return True

    async def _kill_pid(self, pid: int, timeout: float = 10.0) -> int:
        """Kill a process by PID directly (kills entire process group)."""
        import os
        import signal

        try:
            # Kill the process group (negative PID) for graceful termination
            # This ensures child processes are also terminated
            try:
                os.killpg(pid, signal.SIGTERM)
            except ProcessLookupError:
                # Process group might not exist, try regular kill
                os.kill(pid, signal.SIGTERM)

            # Wait for process to exit
            for _ in range(int(timeout * 10)):
                await asyncio.sleep(0.1)
                if not self._is_pid_running(pid):
                    return 0

            # Force kill if still running
            try:
                os.killpg(pid, signal.SIGKILL)
            except ProcessLookupError:
                os.kill(pid, signal.SIGKILL)
            await asyncio.sleep(0.1)
            return -9

        except ProcessLookupError:
            return 0
        except PermissionError:
            return -1

    def _process_to_dict(self, process: Process) -> dict[str, Any]:
        """Convert a Process to a dict for JSON output."""
        return {
            "id": process._id,
            "name": process.name,
            "display_name": process.display_name,
            "command": process.command,
            "context_type": process.context_type,
            "status": process.status,
            "pid": process.pid,
            "uptime_seconds": process.uptime_seconds,
            "exit_code": process.exit_code,
            "error_message": process.error_message,
        }

    async def logs(
        self,
        name: str,
        tail: int = 100,
        since: str | None = None,
    ) -> dict[str, Any]:
        """
        Get logs for a process.

        Args:
            name: Process name
            tail: Number of lines to return (most recent)
            since: Time filter (e.g., '5m', '1h', ISO timestamp)

        Returns a dict with logs (for JSON output).
        """
        init_database()
        process = self._get_process_by_name(name)

        if not process:
            return {
                "success": False,
                "error": f"Process '{name}' not found",
                "error_code": "process_not_found",
            }

        # Build query for logs
        query = LogEntry.query().filter(F("process_id") == process._id)

        # Apply time filter if specified
        if since:
            try:
                seconds_ago = parse_duration(since)
                cutoff = datetime.now() - timedelta(seconds=seconds_ago)
                cutoff_str = cutoff.isoformat()
                query = query.filter(F("timestamp") >= cutoff_str)
            except ValueError as e:
                return {
                    "success": False,
                    "error": str(e),
                    "error_code": "invalid_duration",
                }

        # Get logs ordered by timestamp descending, limited by tail
        # sqler doesn't have ORDER BY in query builder, so we fetch all and sort in Python
        all_logs = query.all()

        # Sort by timestamp descending
        all_logs.sort(key=lambda x: x.timestamp or "", reverse=True)

        # Take the last `tail` entries and reverse for chronological order
        logs_subset = all_logs[:tail]
        logs_subset.reverse()

        log_entries = [
            {
                "timestamp": entry.timestamp,
                "stream": entry.stream,
                "line": entry.line,
            }
            for entry in logs_subset
        ]

        return {
            "success": True,
            "data": {
                "process": name,
                "logs": log_entries,
                "count": len(log_entries),
            },
        }

    async def exec_command(
        self,
        command: str,
        context_type: str = "local",
        container_name: str | None = None,
        cwd: str | None = None,
        timeout: float = 60.0,
    ) -> dict[str, Any]:
        """
        Execute an arbitrary command.

        Args:
            command: The command to execute
            context_type: Execution context ('local' or 'docker')
            container_name: Docker container name (required if context=docker)
            cwd: Working directory
            timeout: Maximum execution time in seconds

        Returns a dict with execution result (for JSON output).
        """
        init_database()

        if context_type == "docker":
            if not container_name:
                return {
                    "success": False,
                    "error": "Container name required for docker context",
                    "error_code": "missing_container",
                    "suggestion": "Use --container <name> to specify the Docker container",
                }

            if not is_docker_available():
                return {
                    "success": False,
                    "error": "Docker is not available",
                    "error_code": "docker_unavailable",
                    "suggestion": "Ensure Docker is installed and running",
                }

        try:
            context = self._get_context(context_type)
        except ValueError as e:
            return {
                "success": False,
                "error": str(e),
                "error_code": "invalid_context",
            }

        try:
            # Docker context needs container_name parameter
            if context_type == "docker":
                result: ExecResult = await context.exec_command(
                    command=command,
                    cwd=cwd,
                    timeout=timeout,
                    container_name=container_name,
                )
            else:
                result: ExecResult = await context.exec_command(
                    command=command,
                    cwd=cwd,
                    timeout=timeout,
                )

            return {
                "success": True,
                "data": {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "exit_code": result.exit_code,
                },
            }

        except ValueError as e:
            # Container not found or similar
            return {
                "success": False,
                "error": str(e),
                "error_code": "container_not_found",
                "suggestion": "Run 'docker ps' to list available containers",
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to execute command: {e}",
                "error_code": "exec_failed",
            }

    def rotate_logs(self, process_id: int, max_entries: int = DEFAULT_MAX_LOGS) -> int:
        """
        Rotate logs for a process, keeping only the most recent entries.

        Args:
            process_id: The process ID
            max_entries: Maximum number of log entries to keep

        Returns the number of entries deleted.
        """
        init_database()

        # Get all logs for this process
        all_logs = LogEntry.query().filter(F("process_id") == process_id).all()

        if len(all_logs) <= max_entries:
            return 0

        # Sort by timestamp descending
        all_logs.sort(key=lambda x: x.timestamp or "", reverse=True)

        # Keep the most recent max_entries, delete the rest
        logs_to_delete = all_logs[max_entries:]
        deleted_count = 0

        for log in logs_to_delete:
            log.delete()
            deleted_count += 1

        return deleted_count

    def cleanup_all_logs(self, max_entries_per_process: int = DEFAULT_MAX_LOGS) -> dict[str, int]:
        """
        Rotate logs for all processes.

        Returns a dict mapping process names to deleted counts.
        """
        init_database()

        processes = Process.query().all()
        results = {}

        for process in processes:
            deleted = self.rotate_logs(process._id, max_entries_per_process)
            if deleted > 0:
                results[process.name] = deleted

        return results


# Global singleton
_manager: ProcessManager | None = None


def get_process_manager() -> ProcessManager:
    """Get the global ProcessManager instance."""
    global _manager
    if _manager is None:
        _manager = ProcessManager()
    return _manager
