"""Central process manager coordinating all process operations."""

import asyncio
import logging
import os
import shlex
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

from sqler.query import SQLerField as F

from ..config import ChangelogAction, append_changelog
from ..db import init_database
from ..models import LogEntry, Process, ProcessStatus
from .context_base import ExecResult, ExecutionContext, ProcessHandle
from .context_docker import get_docker_context, is_docker_available
from .context_local import get_local_context
from .daemon_detector import get_daemon_detector
from .events import EVENT_LOG_ENTRY, EVENT_STATUS_CHANGE, get_event_bus
from .variable_substitution import substitute_vars_from_config

# Default max log entries per process
DEFAULT_MAX_LOGS = 10000

# Default log directory (inside container for docker, on host for local)
DEFAULT_LOG_DIR = "/tmp/procler"

# Linux process state descriptions
LINUX_PROCESS_STATES = {
    "R": {"name": "running", "description": "Running or runnable (on run queue)"},
    "S": {"name": "sleeping", "description": "Interruptible sleep (waiting for event)"},
    "D": {
        "name": "disk_sleep",
        "description": "Uninterruptible sleep (usually I/O) - CANNOT BE KILLED",
    },
    "Z": {"name": "zombie", "description": "Zombie - terminated but not reaped by parent"},
    "T": {"name": "stopped", "description": "Stopped by job control signal"},
    "t": {"name": "tracing_stop", "description": "Stopped by debugger during tracing"},
    "X": {"name": "dead", "description": "Dead (should never be seen)"},
    "I": {"name": "idle", "description": "Idle kernel thread"},
    "W": {"name": "waking", "description": "Waking (Linux 2.6.33 to 3.13 only)"},
    "P": {"name": "parked", "description": "Parked (Linux 3.9 to 3.13 only)"},
}


def get_linux_process_state(pid: int) -> dict[str, Any] | None:
    """
    Read the process state from /proc/[pid]/stat.

    Returns a dict with:
        - state_code: Single letter (R, S, D, Z, T, etc.)
        - state_name: Human-readable name
        - state_description: Full description
        - is_killable: False if in D state

    Returns None if the process doesn't exist or can't be read.
    """
    try:
        stat_path = Path(f"/proc/{pid}/stat")
        if not stat_path.exists():
            return None

        content = stat_path.read_text()

        # Format: pid (comm) state ppid ...
        # comm can contain spaces and parentheses, so find the last )
        last_paren = content.rfind(")")
        if last_paren == -1:
            return None

        # State is the first character after ") "
        state_section = content[last_paren + 2 :]
        state_code = state_section.split()[0]

        state_info = LINUX_PROCESS_STATES.get(
            state_code, {"name": "unknown", "description": f"Unknown state: {state_code}"}
        )

        return {
            "state_code": state_code,
            "state_name": state_info["name"],
            "state_description": state_info["description"],
            "is_killable": state_code != "D",
        }

    except (OSError, IndexError):
        return None


def get_process_children(pid: int) -> list[int]:
    """Get all child PIDs of a process."""
    children = []
    try:
        children_path = Path(f"/proc/{pid}/task/{pid}/children")
        if children_path.exists():
            content = children_path.read_text().strip()
            if content:
                children = [int(p) for p in content.split()]
    except (OSError, ValueError):
        pass
    return children


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
        "s": 1,
        "m": 60,
        "h": 3600,
        "d": 86400,
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


def get_log_file_path(process_name: str) -> str:
    """Get the default log file path for a process."""
    # Sanitize process name for filename (replace unsafe chars)
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in process_name)
    return f"{DEFAULT_LOG_DIR}/{safe_name}.log"


def extract_docker_exec_user(command: str) -> str | None:
    """Extract the -u/--user value from a docker exec command."""
    import re

    # Match -u <user> or --user <user> or --user=<user>
    match = re.search(r"(?:-u|--user)[=\s]+([^\s]+)", command)
    return match.group(1) if match else None


def ensure_log_dir_in_container(container: str, user: str | None = None) -> None:
    """Ensure log directory exists inside a Docker container.

    If user is provided, creates directory as that user so they can write to it.
    """
    import subprocess

    try:
        cmd = ["docker", "exec"]
        if user:
            cmd.extend(["-u", user])
        cmd.extend([container, "mkdir", "-p", DEFAULT_LOG_DIR])
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError:
        pass  # Best effort - directory might already exist or container might be unavailable


def ensure_local_log_dir() -> None:
    """Ensure log directory exists on local filesystem."""
    Path(DEFAULT_LOG_DIR).mkdir(parents=True, exist_ok=True)


async def read_log_file_from_container(container: str, log_path: str, tail: int = 100) -> list[str]:
    """Read log file from inside a Docker container."""
    import subprocess

    try:
        result = subprocess.run(
            ["docker", "exec", container, "tail", "-n", str(tail), log_path],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.splitlines()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        pass
    return []


def wrap_command_with_log_redirect(command: str, log_path: str) -> str:
    """Wrap a command to redirect stdout/stderr to a log file.

    For bash -c commands, we inject the redirect inside the quoted command.
    For other commands, we append the redirect.
    """
    # Quote the log path to prevent shell injection
    safe_log_path = shlex.quote(log_path)

    # Check if this is a bash -c "..." pattern
    if 'bash -c "' in command or "bash -c '" in command:
        # Find the inner command and add redirect there
        # Pattern: ... bash -c "inner_command"
        import re

        # Match bash -c followed by quoted string
        match = re.search(r'(bash -c ["\'])(.+?)(["\'])(\s*)$', command)
        if match:
            prefix = command[: match.start()] + match.group(1)
            inner_cmd = match.group(2)
            quote = match.group(3)
            suffix = match.group(4)
            # Add redirect to inner command (truncate on start with >)
            # Inside bash -c, strip outer quotes from safe_log_path since we're already quoted
            inner_safe_path = safe_log_path[1:-1] if safe_log_path.startswith("'") else safe_log_path
            return f"{prefix}{inner_cmd} > {inner_safe_path} 2>&1{quote}{suffix}"

    # For simple commands, just append redirect
    return f"{command} > {safe_log_path} 2>&1"


class ProcessManager:
    """Central coordinator for process operations."""

    def __init__(self):
        self._contexts: dict[str, ExecutionContext] = {}
        self._handles: dict[int, ProcessHandle] = {}  # process_id -> handle
        self._lock = asyncio.Lock()  # Protects _handles from concurrent access
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

    async def _get_handle(self, process_id: int) -> ProcessHandle | None:
        """Thread-safe get handle."""
        async with self._lock:
            return self._handles.get(process_id)

    async def _set_handle(self, process_id: int, handle: ProcessHandle) -> None:
        """Thread-safe set handle."""
        async with self._lock:
            self._handles[process_id] = handle

    async def _remove_handle(self, process_id: int) -> None:
        """Thread-safe remove handle."""
        async with self._lock:
            self._handles.pop(process_id, None)

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
            try:
                entry.save()
            except Exception as e:
                logger.error(f"Failed to save log entry for process {process_id}: {e}")

            # Emit event for WebSocket broadcast
            try:
                get_event_bus().emit_sync(
                    EVENT_LOG_ENTRY,
                    {
                        "process_id": process_id,
                        "stream": stream,
                        "line": line,
                        "timestamp": timestamp,
                    },
                )
            except Exception as e:
                logger.error(f"Failed to emit log event for process {process_id}: {e}")

        return callback

    def _exit_callback(self, process: Process):
        """Create a callback for process exit."""

        def callback(exit_code: int) -> None:
            # Reload process to get latest state
            try:
                updated = Process.from_id(process._id)
            except Exception as e:
                logger.error(f"Failed to reload process {process._id} on exit: {e}")
                self._handles.pop(process._id, None)
                return

            if updated:
                updated.status = ProcessStatus.STOPPED.value
                updated.exit_code = exit_code
                updated.pid = None
                try:
                    updated.save()
                except Exception as e:
                    logger.error(f"Failed to save process {process._id} on exit: {e}")

                # Remove handle (use pop() to avoid race with concurrent access)
                self._handles.pop(process._id, None)

                # Emit status change event
                try:
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
                except Exception as e:
                    logger.error(f"Failed to emit exit event for process {process._id}: {e}")

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
                "suggestion": "Use 'procler list' to see available processes, or 'procler define' to create one",
            }

        # Check if already running
        if process.status == ProcessStatus.RUNNING.value:
            is_running = False
            handle = await self._get_handle(process._id)
            if handle:
                context = self._get_context(process.context_type)
                is_running = await context.is_running(handle)
            elif process.pid:
                # No handle but we have a PID - check in the correct context
                is_running = await self._is_process_pid_running(process)

            if is_running:
                return {
                    "success": True,
                    "data": {
                        "status": "already_running",
                        "process": self._process_to_dict(process),
                    },
                }

        # Daemon mode: Check if we should adopt an existing daemon
        if getattr(process, "daemon_mode", False) and getattr(process, "adopt_existing", False):
            detector = get_daemon_detector()
            # Determine container for daemon detection
            # Use daemon_container if set, otherwise fall back to container_name for docker context
            raw_container = getattr(process, "daemon_container", None) or (
                process.container_name if process.context_type == "docker" else None
            )
            # Substitute vars in container name (e.g., ${SIM_CONTAINER})
            container = substitute_vars_from_config(raw_container) if raw_container else None
            # Try to find existing daemon
            existing_pid = await detector.find_daemon_pid(
                pattern=getattr(process, "daemon_match_pattern", None),
                pidfile=getattr(process, "daemon_pidfile", None),
                container=container,
            )
            if existing_pid:
                # Adopt the existing daemon
                process.status = ProcessStatus.RUNNING.value
                process.pid = existing_pid
                process.started_at = datetime.now().isoformat()
                process.adopted = True

                # Set up log_file path for adopted processes
                # Note: We can't redirect output of already-running processes,
                # but setting the path allows logs() to look for it and shows
                # users where logs would go if they restart via procler
                log_file_path = getattr(process, "log_file", None) or get_log_file_path(process.name)
                process.log_file = log_file_path
                process.save()

                append_changelog(
                    action=ChangelogAction.START,
                    entity_type="process",
                    entity_name=name,
                    details={
                        "pid": existing_pid,
                        "adopted": True,
                        "context": process.context_type,
                    },
                )

                return {
                    "success": True,
                    "data": {
                        "status": "adopted",
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
                "suggestion": "Valid context types are 'local' or 'docker'. Check process definition.",
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
            # Substitute config vars in command (e.g., ${SIM_CONTAINER})
            resolved_command = substitute_vars_from_config(process.command)

            # Set up log file for daemon processes
            log_file_path = None
            if getattr(process, "daemon_mode", False):
                log_file_path = getattr(process, "log_file", None) or get_log_file_path(process.name)
                # Get container for log directory creation
                raw_daemon_container = getattr(process, "daemon_container", None)
                daemon_container = substitute_vars_from_config(raw_daemon_container) if raw_daemon_container else None

                # Ensure log directory exists (as the user who will run the process)
                if daemon_container:
                    # Extract user from docker exec command (e.g., -u 1000)
                    exec_user = extract_docker_exec_user(resolved_command)
                    ensure_log_dir_in_container(daemon_container, user=exec_user)
                else:
                    ensure_local_log_dir()

                # Wrap command to redirect output to log file
                resolved_command = wrap_command_with_log_redirect(resolved_command, log_file_path)

                # Store log file path
                process.log_file = log_file_path

            # Start the process (Docker context needs container_name)
            if process.context_type == "docker":
                handle = await context.start_process(
                    command=resolved_command,
                    cwd=process.cwd,
                    env=process.env,
                    on_stdout=self._log_callback(process._id, "stdout"),
                    on_stderr=self._log_callback(process._id, "stderr"),
                    on_exit=self._exit_callback(process),
                    container_name=process.container_name,
                )
            else:
                handle = await context.start_process(
                    command=resolved_command,
                    cwd=process.cwd,
                    env=process.env,
                    on_stdout=self._log_callback(process._id, "stdout"),
                    on_stderr=self._log_callback(process._id, "stderr"),
                    on_exit=self._exit_callback(process),
                )

            # Daemon mode: Wait for fork and find real daemon PID
            daemon_pid = handle.pid
            if getattr(process, "daemon_mode", False):
                pattern = getattr(process, "daemon_match_pattern", None)
                pidfile = getattr(process, "daemon_pidfile", None)
                if pattern or pidfile:
                    detector = get_daemon_detector()
                    # Use daemon_container if set, otherwise fall back to container_name
                    raw_container = getattr(process, "daemon_container", None) or (
                        process.container_name if process.context_type == "docker" else None
                    )
                    # Substitute vars in container name (e.g., ${SIM_CONTAINER})
                    container = substitute_vars_from_config(raw_container) if raw_container else None
                    # Wait for daemon to fork and find its real PID
                    found_pid = await detector.wait_for_fork(
                        pattern=pattern or "",
                        container=container,
                        timeout=5.0,
                    )
                    if found_pid:
                        daemon_pid = found_pid

            # Update process state
            process.status = ProcessStatus.RUNNING.value
            process.pid = daemon_pid
            process.started_at = datetime.now().isoformat()
            process.exit_code = None
            process.error_message = None
            process.save()

            # Store handle (thread-safe)
            await self._set_handle(process._id, handle)

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

            # Log to changelog
            append_changelog(
                action=ChangelogAction.START,
                entity_type="process",
                entity_name=name,
                details={"pid": process.pid, "context": process.context_type},
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
                "suggestion": "Use 'procler list' to see available processes, or 'procler define' to create one",
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

        handle = await self._get_handle(process._id)

        # Update status to stopping
        process.status = ProcessStatus.STOPPING.value
        process.save()

        try:
            exit_code = 0

            # Daemon mode with container: Kill daemon inside container
            raw_daemon_container = getattr(process, "daemon_container", None)
            # Substitute vars in container name (e.g., ${SIM_CONTAINER})
            daemon_container = substitute_vars_from_config(raw_daemon_container) if raw_daemon_container else None
            if getattr(process, "daemon_mode", False) and daemon_container and process.pid:
                exit_code = await self._kill_daemon_in_container(
                    container=daemon_container,
                    pid=process.pid,
                    timeout=timeout,
                )
            elif process.pid and self._is_pid_running(process.pid):
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

            # Remove handle (thread-safe)
            await self._remove_handle(process._id)

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

            # Log to changelog
            append_changelog(
                action=ChangelogAction.STOP,
                entity_type="process",
                entity_name=name,
                details={"exit_code": exit_code},
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

    async def restart(
        self,
        name: str,
        timeout: float = 10.0,
        clear_logs: bool = False,
    ) -> dict[str, Any]:
        """
        Restart a process by name (stop then start).

        Args:
            name: Process name
            timeout: Seconds to wait for stop
            clear_logs: If True, delete old logs before starting

        Returns a dict with status and process info (for JSON output).
        """
        init_database()
        process = self._get_process_by_name(name)

        if not process:
            return {
                "success": False,
                "error": f"Process '{name}' not found",
                "error_code": "process_not_found",
                "suggestion": "Use 'procler list' to see available processes, or 'procler define' to create one",
            }

        # Stop if running
        if process.status in [ProcessStatus.RUNNING.value, ProcessStatus.STARTING.value]:
            stop_result = await self.stop(name, timeout=timeout)
            if not stop_result["success"]:
                return stop_result

        # Clear old logs if requested
        if clear_logs and process._id:
            LogEntry.delete().where(F("process_id") == process._id).execute()

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
        """Verify and update the running status of a process.

        For daemon processes, this also auto-adopts running daemons even if
        the process is marked as stopped.
        """
        # Daemon mode: Use daemon detector to find/verify PID
        # Check daemon status regardless of current status (to auto-adopt)
        if getattr(process, "daemon_mode", False):
            pattern = getattr(process, "daemon_match_pattern", None)
            pidfile = getattr(process, "daemon_pidfile", None)
            if pattern or pidfile:
                detector = get_daemon_detector()
                # Use daemon_container if set, otherwise fall back to container_name
                raw_container = getattr(process, "daemon_container", None) or (
                    process.container_name if process.context_type == "docker" else None
                )
                # Substitute vars in container name (e.g., ${SIM_CONTAINER})
                container = substitute_vars_from_config(raw_container) if raw_container else None
                found_pid = await detector.find_daemon_pid(
                    pattern=pattern,
                    pidfile=pidfile,
                    container=container,
                )
                if found_pid:
                    # Daemon is running - update status and PID
                    if process.status != ProcessStatus.RUNNING.value or process.pid != found_pid:
                        process.status = ProcessStatus.RUNNING.value
                        process.pid = found_pid
                        if not process.started_at:
                            process.started_at = datetime.now().isoformat()
                        # Set log_file path for auto-adopted processes
                        if not getattr(process, "log_file", None):
                            process.log_file = get_log_file_path(process.name)
                            process.adopted = True
                        process.save()
                    return
                else:
                    # Daemon not found - mark as stopped
                    if process.status == ProcessStatus.RUNNING.value:
                        process.status = ProcessStatus.STOPPED.value
                        process.pid = None
                        await self._remove_handle(process._id)
                        process.save()
                    return

        # Non-daemon: Only verify if currently marked as running
        if process.status != ProcessStatus.RUNNING.value:
            return

        # Non-daemon mode: Use handle or PID check
        handle = await self._get_handle(process._id)
        if handle:
            # We have a handle, check via context
            context = self._get_context(process.context_type)
            if not await context.is_running(handle):
                process.status = ProcessStatus.STOPPED.value
                process.pid = None
                process.save()
                await self._remove_handle(process._id)
        elif process.pid:
            # No handle but we have a PID - check in the correct context
            is_running = await self._is_process_pid_running(process)
            if not is_running:
                process.status = ProcessStatus.STOPPED.value
                process.pid = None
                process.save()
        else:
            # No handle and no PID - mark as stopped
            process.status = ProcessStatus.STOPPED.value
            process.save()

    def _is_pid_running(self, pid: int) -> bool:
        """Check if a PID is still running in the OS."""

        try:
            os.kill(pid, 0)  # Signal 0 just checks if process exists
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            # Process exists but we don't have permission to signal it
            return True

    async def _is_process_pid_running(self, process: Process) -> bool:
        """Check if a process PID is running in its execution context."""
        if not process.pid:
            return False

        if process.context_type == "docker":
            raw_container = getattr(process, "daemon_container", None) or process.container_name
            container = substitute_vars_from_config(raw_container) if raw_container else None
            if container:
                detector = get_daemon_detector()
                return await detector.is_pid_running(process.pid, container=container)

        return self._is_pid_running(process.pid)

    async def _kill_pid(self, pid: int, timeout: float = 10.0) -> int:
        """Kill a process by PID directly (kills entire process group)."""
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

    async def _kill_daemon_in_container(self, container: str, pid: int, timeout: float = 10.0) -> int:
        """Kill a daemon process inside a Docker container."""
        import logging

        logger = logging.getLogger(__name__)

        try:
            # Send SIGTERM to daemon
            cmd = f"docker exec {container} kill -TERM {pid}"
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()

            # Wait for daemon to exit
            detector = get_daemon_detector()
            for _ in range(int(timeout * 10)):
                await asyncio.sleep(0.1)
                if not await detector.is_pid_running(pid, container=container):
                    logger.debug(f"Daemon PID {pid} in {container} stopped gracefully")
                    return 0

            # Force kill if still running
            cmd = f"docker exec {container} kill -KILL {pid}"
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            await asyncio.sleep(0.1)
            logger.debug(f"Daemon PID {pid} in {container} force killed")
            return -9

        except Exception as e:
            logger.error(f"Error killing daemon {pid} in {container}: {e}")
            return -1

    def _process_to_dict(self, process: Process) -> dict[str, Any]:
        """Convert a Process to a dict for JSON output."""
        result = {
            "id": process._id,
            "name": process.name,
            "display_name": process.display_name,
            "command": process.command,
            "context_type": process.context_type,
            "context": process.context_type,
            "container": process.container_name,
            "cwd": process.cwd,
            "tags": process.tags,
            "created_at": process.created_at,
            "updated_at": process.updated_at,
            "status": process.status,
            "pid": process.pid,
            "uptime_seconds": process.uptime_seconds,
            "exit_code": process.exit_code,
            "error_message": process.error_message,
            # Daemon mode fields
            "daemon_mode": getattr(process, "daemon_mode", False) or None,
            "daemon_match_pattern": getattr(process, "daemon_match_pattern", None),
            "daemon_container": getattr(process, "daemon_container", None),
            "log_file": getattr(process, "log_file", None),
            "adopted": getattr(process, "adopted", False) or None,
        }

        # Add Linux process state if running and we have a PID
        if process.pid and process.status == ProcessStatus.RUNNING.value:
            linux_state = get_linux_process_state(process.pid)
            if linux_state:
                result["linux_state"] = linux_state
                # Add warning for problematic states
                if linux_state["state_code"] == "D":
                    result["warning"] = "Process in uninterruptible sleep (D state) - may be stuck on I/O"
                elif linux_state["state_code"] == "Z":
                    result["warning"] = "Process is a zombie - parent has not reaped it"
                elif linux_state["state_code"] == "T":
                    result["warning"] = "Process is stopped (possibly by debugger or signal)"

        return result

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
                "suggestion": "Use 'procler list' to see available processes, or 'procler define' to create one",
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

        # For daemon processes with log_file, prefer file over database
        # (database may have stale entries from previous runs)
        log_source = "database"
        log_file = getattr(process, "log_file", None)
        is_daemon = getattr(process, "daemon_mode", False)

        # Try log file for daemon processes or when database is empty
        if log_file and (is_daemon or not log_entries):
            # Determine if we need to read from container
            raw_daemon_container = getattr(process, "daemon_container", None)
            daemon_container = substitute_vars_from_config(raw_daemon_container) if raw_daemon_container else None

            if daemon_container:
                # Read from log file inside container
                lines = await read_log_file_from_container(daemon_container, log_file, tail)
            else:
                # Read from local log file
                try:
                    log_path = Path(log_file)
                    if log_path.exists():
                        with open(log_path) as f:
                            all_lines = f.readlines()
                            lines = [line.rstrip("\n") for line in all_lines[-tail:]]
                    else:
                        lines = []
                except OSError:
                    lines = []

            if lines:
                log_source = "file"
                log_entries = [
                    {
                        "timestamp": None,
                        "stream": "stdout",
                        "line": line,
                    }
                    for line in lines
                ]

        result_data = {
            "process": name,
            "logs": log_entries,
            "count": len(log_entries),
            "source": log_source,
            "log_file": log_file,
        }

        # Add helpful message for adopted processes with no logs
        is_adopted = getattr(process, "adopted", False)
        if is_adopted and not log_entries:
            result_data["adopted"] = True
            result_data["note"] = (
                "This process was adopted (found already running). "
                "Historical logs are not available. Restart via 'procler restart' to capture logs."
            )
        elif is_adopted:
            result_data["adopted"] = True

        return {
            "success": True,
            "data": result_data,
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
                "suggestion": "Valid context types are 'local' or 'docker'",
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
