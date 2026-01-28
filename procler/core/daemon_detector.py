"""Daemon detection module for tracking forking daemons.

This module provides functionality to detect and track daemon processes
that fork to background after starting. It supports two detection methods:
1. Pidfile-based detection (daemon writes PID to file)
2. Process name pattern matching (grep ps aux output)
"""

from __future__ import annotations

import asyncio
import logging
import shlex
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)


def _quote_user(user: str | int | None) -> str:
    """Quote user parameter for shell commands."""
    if user is None:
        return "1000"
    return shlex.quote(str(user))


@dataclass
class ProcessInfo:
    """Information about a detected process."""

    pid: int
    command: str
    user: str | None = None


class DaemonDetector:
    """Detects and tracks daemon processes after fork.

    This class provides methods to find daemon PIDs using either pidfile
    reading or process name pattern matching. It works with both local
    processes and processes running inside Docker containers.
    """

    async def find_daemon_pid(
        self,
        pattern: str | None = None,
        pidfile: str | None = None,
        container: str | None = None,
        user: str | int | None = None,
    ) -> int | None:
        """Find daemon PID using pidfile or pattern matching.

        Tries pidfile first if specified, falls back to pattern matching.

        Args:
            pattern: Process name pattern to grep for (e.g., "msgd")
            pidfile: Path to pidfile containing daemon PID
            container: Docker container name (None for local processes)
            user: User to run as in container (e.g., 1000 or "product")

        Returns:
            The daemon's PID if found, None otherwise
        """
        # Try pidfile first if specified
        if pidfile:
            pid = await self._read_pidfile(pidfile, container, user)
            if pid:
                logger.debug(f"Found daemon PID {pid} from pidfile {pidfile}")
                return pid
            logger.debug(f"Pidfile {pidfile} not found or empty, trying pattern")

        # Fall back to pattern matching
        if pattern:
            pid = await self._find_by_pattern(pattern, container, user)
            if pid:
                logger.debug(f"Found daemon PID {pid} by pattern '{pattern}'")
                return pid

        logger.debug("Daemon not found by any method")
        return None

    async def wait_for_fork(
        self,
        pattern: str,
        container: str | None = None,
        user: str | int | None = None,
        timeout: float = 5.0,
        poll_interval: float = 0.2,
    ) -> int | None:
        """Wait for daemon to fork from parent process.

        Polls for the daemon process until it appears or timeout.
        Use this after starting a daemon that forks to background.

        Args:
            pattern: Process name pattern to grep for
            container: Docker container name (None for local processes)
            user: User to run as in container
            timeout: Maximum time to wait in seconds
            poll_interval: Time between polls in seconds

        Returns:
            The daemon's PID if found within timeout, None otherwise
        """
        start_time = time.monotonic()
        attempts = 0

        while (time.monotonic() - start_time) < timeout:
            attempts += 1
            pid = await self._find_by_pattern(pattern, container, user)
            if pid:
                logger.debug(f"Found forked daemon PID {pid} after {attempts} attempts")
                return pid
            await asyncio.sleep(poll_interval)

        logger.warning(f"Daemon with pattern '{pattern}' not found after {timeout}s " f"({attempts} attempts)")
        return None

    async def is_pid_running(
        self,
        pid: int,
        container: str | None = None,
        user: str | int | None = None,
    ) -> bool:
        """Check if a PID is currently running.

        Args:
            pid: Process ID to check
            container: Docker container name (None for local processes)
            user: User to run as in container

        Returns:
            True if process is running, False otherwise
        """
        if container:
            cmd = f"docker exec -u {_quote_user(user)} {shlex.quote(container)} ps -p {pid}"
        else:
            cmd = f"ps -p {pid}"

        try:
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            return proc.returncode == 0
        except Exception as e:
            logger.error(f"Error checking PID {pid}: {e}")
            return False

    async def list_processes(
        self,
        container: str | None = None,
        user: str | int | None = None,
    ) -> list[ProcessInfo]:
        """List all processes (for debugging/inspection).

        Args:
            container: Docker container name (None for local processes)
            user: User to run as in container

        Returns:
            List of ProcessInfo objects for all running processes
        """
        if container:
            cmd = f"docker exec -u {_quote_user(user)} {shlex.quote(container)} ps aux"
        else:
            cmd = "ps aux"

        try:
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()

            processes = []
            for line in stdout.decode().strip().split("\n")[1:]:  # Skip header
                parts = line.split(None, 10)  # Split into max 11 parts
                if len(parts) >= 11:
                    processes.append(
                        ProcessInfo(
                            pid=int(parts[1]),
                            command=parts[10],
                            user=parts[0],
                        )
                    )
            return processes
        except Exception as e:
            logger.error(f"Error listing processes: {e}")
            return []

    async def _read_pidfile(
        self,
        pidfile: str,
        container: str | None = None,
        user: str | int | None = None,
    ) -> int | None:
        """Read PID from a pidfile.

        Args:
            pidfile: Path to the pidfile
            container: Docker container name (None for local processes)
            user: User to run as in container

        Returns:
            The PID from the file, or None if file doesn't exist/is invalid
        """
        # Validate pidfile path - reject path traversal attempts
        if ".." in pidfile or pidfile.startswith("/etc/") or pidfile.startswith("/root/"):
            logger.warning(f"Suspicious pidfile path rejected: {pidfile}")
            return None

        if container:
            cmd = f"docker exec -u {_quote_user(user)} {shlex.quote(container)} cat {shlex.quote(pidfile)}"
        else:
            cmd = f"cat {shlex.quote(pidfile)}"

        try:
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()

            if proc.returncode == 0:
                pid_str = stdout.decode().strip()
                if pid_str.isdigit():
                    pid = int(pid_str)
                    # Verify PID is actually running
                    if await self.is_pid_running(pid, container, user):
                        return pid
                    logger.debug(f"PID {pid} from pidfile is not running")
            return None
        except Exception as e:
            logger.error(f"Error reading pidfile {pidfile}: {e}")
            return None

    async def _find_by_pattern(
        self,
        pattern: str,
        container: str | None = None,
        user: str | int | None = None,
    ) -> int | None:
        """Find process PID by pattern matching.

        Uses ps aux | grep to find processes matching the pattern.
        Takes the first (oldest) match if multiple exist.

        Args:
            pattern: Process name pattern to grep for
            container: Docker container name (None for local processes)
            user: User to run as in container

        Returns:
            The PID of the matching process, or None if not found
        """
        # Use bracket trick to avoid matching grep itself
        # e.g., "msgd" becomes "[m]sgd"
        safe_pattern = self._make_grep_pattern(pattern)

        # Escape pattern for shell - use shlex.quote and strip outer quotes for grep
        # since we're already inside quotes
        escaped_pattern = shlex.quote(safe_pattern)[1:-1]  # Remove outer quotes added by shlex

        if container:
            docker_cmd = f"docker exec -u {_quote_user(user)} {shlex.quote(container)}"
            cmd = f"{docker_cmd} bash -c \"ps aux | grep '{escaped_pattern}'\""
        else:
            cmd = f"ps aux | grep '{escaped_pattern}'"

        try:
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()

            if proc.returncode == 0 and stdout:
                # Take the first line (oldest process)
                lines = stdout.decode().strip().split("\n")
                if lines and lines[0]:
                    parts = lines[0].split()
                    if len(parts) >= 2:
                        try:
                            return int(parts[1])  # PID is second column
                        except ValueError:
                            pass
            return None
        except Exception as e:
            logger.error(f"Error finding process by pattern '{pattern}': {e}")
            return None

    def _make_grep_pattern(self, pattern: str) -> str:
        """Convert pattern to grep-safe format using bracket trick.

        The bracket trick prevents grep from matching its own process.
        e.g., "msgd" becomes "[m]sgd"

        Args:
            pattern: Original pattern string

        Returns:
            Pattern with first character in brackets
        """
        if not pattern:
            return pattern
        # Put first character in brackets to avoid self-match
        return f"[{pattern[0]}]{pattern[1:]}"


# Singleton instance
_detector: DaemonDetector | None = None


def get_daemon_detector() -> DaemonDetector:
    """Get the singleton DaemonDetector instance."""
    global _detector
    if _detector is None:
        _detector = DaemonDetector()
    return _detector
