"""Log file tailer for live streaming of daemon process logs."""

import asyncio
import logging
from datetime import datetime
from pathlib import Path

from ..models import Process
from .events import EVENT_LOG_ENTRY, get_event_bus
from .variable_substitution import substitute_vars_from_config

logger = logging.getLogger(__name__)

# Polling interval for file changes (seconds)
POLL_INTERVAL = 0.5

# Maximum lines to read per poll (prevents memory issues)
MAX_LINES_PER_POLL = 1000


class LogFileTailer:
    """Tails log files and emits events for new lines.

    This enables live log streaming for daemon processes that write to log files
    instead of having their stdout/stderr captured directly.
    """

    def __init__(self):
        # process_id -> tail task
        self._watchers: dict[int, asyncio.Task] = {}
        # process_id -> last file position (bytes)
        self._positions: dict[int, int] = {}

    async def start_tailing(self, process: Process) -> bool:
        """Start tailing a process's log file.

        Args:
            process: The process to tail logs for

        Returns:
            True if tailing started, False if not applicable
        """
        process_id = process._id
        log_file = getattr(process, "log_file", None)

        if not log_file:
            logger.debug(f"Process {process.name} has no log_file, skipping tail")
            return False

        # Already tailing this process
        if process_id in self._watchers:
            logger.debug(f"Already tailing process {process.name}")
            return True

        # Determine if we need to tail from container or locally
        raw_container = getattr(process, "daemon_container", None)
        container = substitute_vars_from_config(raw_container) if raw_container else None

        # Start at end of file (don't replay history - that's what logs() is for)
        if container:
            initial_size = await self._get_container_file_size(container, log_file)
        else:
            initial_size = self._get_local_file_size(log_file)

        self._positions[process_id] = initial_size

        # Create tail task
        if container:
            task = asyncio.create_task(self._tail_container_file(process_id, process.name, container, log_file))
        else:
            task = asyncio.create_task(self._tail_local_file(process_id, process.name, log_file))

        self._watchers[process_id] = task
        logger.info(f"Started tailing logs for {process.name} ({log_file})")
        return True

    async def stop_tailing(self, process_id: int) -> None:
        """Stop tailing a process's log file.

        Args:
            process_id: The process ID to stop tailing
        """
        task = self._watchers.pop(process_id, None)
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            logger.debug(f"Stopped tailing logs for process {process_id}")

        self._positions.pop(process_id, None)

    def is_tailing(self, process_id: int) -> bool:
        """Check if we're currently tailing a process."""
        return process_id in self._watchers

    async def stop_all(self) -> None:
        """Stop all active tailers."""
        for process_id in list(self._watchers.keys()):
            await self.stop_tailing(process_id)

    def _get_local_file_size(self, file_path: str) -> int:
        """Get the current size of a local file."""
        try:
            return Path(file_path).stat().st_size
        except OSError:
            return 0

    async def _get_container_file_size(self, container: str, file_path: str) -> int:
        """Get the current size of a file inside a Docker container."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "docker",
                "exec",
                container,
                "stat",
                "-c",
                "%s",
                file_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            if proc.returncode == 0:
                return int(stdout.decode().strip())
        except (ValueError, OSError):
            pass
        return 0

    async def _tail_local_file(self, process_id: int, process_name: str, file_path: str) -> None:
        """Tail a local log file using polling."""
        logger.debug(f"Starting local file tail for {process_name}: {file_path}")

        while True:
            try:
                await asyncio.sleep(POLL_INTERVAL)

                current_size = self._get_local_file_size(file_path)
                last_position = self._positions.get(process_id, 0)

                # File was truncated (e.g., log rotation)
                if current_size < last_position:
                    logger.debug(f"Log file {file_path} was truncated, resetting position")
                    last_position = 0

                # No new content
                if current_size <= last_position:
                    continue

                # Read new content
                try:
                    with open(file_path, "rb") as f:
                        f.seek(last_position)
                        new_content = f.read(current_size - last_position)
                        self._positions[process_id] = f.tell()
                except OSError as e:
                    logger.debug(f"Error reading {file_path}: {e}")
                    continue

                # Emit each new line
                await self._emit_lines(process_id, new_content)

            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.debug(f"Error tailing {file_path}: {e}")
                await asyncio.sleep(POLL_INTERVAL)

    async def _tail_container_file(self, process_id: int, process_name: str, container: str, file_path: str) -> None:
        """Tail a log file inside a Docker container using polling."""
        logger.debug(f"Starting container file tail for {process_name}: {container}:{file_path}")

        while True:
            try:
                await asyncio.sleep(POLL_INTERVAL)

                current_size = await self._get_container_file_size(container, file_path)
                last_position = self._positions.get(process_id, 0)

                # File was truncated
                if current_size < last_position:
                    logger.debug(f"Log file {file_path} in {container} was truncated")
                    last_position = 0

                # No new content
                if current_size <= last_position:
                    continue

                # Read new content from container
                # Using tail -c +N reads from byte N onwards
                try:
                    proc = await asyncio.create_subprocess_exec(
                        "docker",
                        "exec",
                        container,
                        "tail",
                        "-c",
                        f"+{last_position + 1}",  # tail uses 1-based offset
                        file_path,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=10.0)
                    if proc.returncode == 0 and stdout:
                        self._positions[process_id] = current_size
                        await self._emit_lines(process_id, stdout)
                except TimeoutError:
                    logger.debug(f"Timeout reading from {container}:{file_path}")
                except OSError as e:
                    logger.debug(f"Error reading from {container}:{file_path}: {e}")

            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.debug(f"Error tailing {container}:{file_path}: {e}")
                await asyncio.sleep(POLL_INTERVAL)

    async def _emit_lines(self, process_id: int, content: bytes) -> None:
        """Emit log entry events for each line in content."""
        try:
            text = content.decode("utf-8", errors="replace")
        except Exception:
            return

        lines = text.splitlines()
        event_bus = get_event_bus()
        timestamp = datetime.now().isoformat()

        line_count = 0
        for line in lines:
            if not line:
                continue
            if line_count >= MAX_LINES_PER_POLL:
                logger.debug(f"Hit max lines per poll ({MAX_LINES_PER_POLL})")
                break

            event_bus.emit_sync(
                EVENT_LOG_ENTRY,
                {
                    "process_id": process_id,
                    "stream": "stdout",
                    "line": line,
                    "timestamp": timestamp,
                },
            )
            line_count += 1


# Global singleton
_tailer: LogFileTailer | None = None


def get_log_tailer() -> LogFileTailer:
    """Get the global LogFileTailer instance."""
    global _tailer
    if _tailer is None:
        _tailer = LogFileTailer()
    return _tailer
