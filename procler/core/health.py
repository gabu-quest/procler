"""Health check management for processes."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable

from ..config import HealthCheckDef
from .context_local import get_local_context


class HealthStatus(str, Enum):
    """Health check status."""
    UNKNOWN = "unknown"  # Never checked
    STARTING = "starting"  # In start_period grace window
    HEALTHY = "healthy"  # Passing health checks
    UNHEALTHY = "unhealthy"  # Failed health checks
    DEAD = "dead"  # Process not running


@dataclass
class HealthState:
    """Current health state for a process."""
    status: HealthStatus
    last_check: datetime | None = None
    consecutive_failures: int = 0
    last_error: str | None = None
    check_count: int = 0


class HealthChecker:
    """
    Manages health checks for processes.

    Runs health check commands at intervals and tracks pass/fail state.
    Supports start_period grace period and configurable retries.
    """

    def __init__(self):
        self._health_states: dict[str, HealthState] = {}
        self._check_tasks: dict[str, asyncio.Task] = {}
        self._callbacks: dict[str, list[Callable[[str, HealthStatus], None]]] = {}
        self._local_context = get_local_context()

    def get_health(self, process_name: str) -> HealthState:
        """Get current health state for a process."""
        return self._health_states.get(
            process_name,
            HealthState(status=HealthStatus.UNKNOWN)
        )

    def register_process(
        self,
        process_name: str,
        healthcheck: HealthCheckDef,
        on_status_change: Callable[[str, HealthStatus], None] | None = None,
    ) -> None:
        """
        Register a process for health checking.

        Args:
            process_name: Name of the process
            healthcheck: Health check definition from config
            on_status_change: Optional callback for status changes
        """
        # Initialize state
        self._health_states[process_name] = HealthState(
            status=HealthStatus.STARTING,
            last_check=None,
            consecutive_failures=0,
        )

        if on_status_change:
            if process_name not in self._callbacks:
                self._callbacks[process_name] = []
            self._callbacks[process_name].append(on_status_change)

    async def start_checking(
        self,
        process_name: str,
        healthcheck: HealthCheckDef,
    ) -> None:
        """Start the health check loop for a process."""
        # Cancel any existing check task
        if process_name in self._check_tasks:
            self._check_tasks[process_name].cancel()
            try:
                await self._check_tasks[process_name]
            except asyncio.CancelledError:
                pass

        # Start new check task
        self._check_tasks[process_name] = asyncio.create_task(
            self._health_check_loop(process_name, healthcheck)
        )

    async def stop_checking(self, process_name: str) -> None:
        """Stop health checking for a process."""
        if process_name in self._check_tasks:
            self._check_tasks[process_name].cancel()
            try:
                await self._check_tasks[process_name]
            except asyncio.CancelledError:
                pass
            del self._check_tasks[process_name]

        if process_name in self._health_states:
            self._health_states[process_name].status = HealthStatus.DEAD

    async def _health_check_loop(
        self,
        process_name: str,
        healthcheck: HealthCheckDef,
    ) -> None:
        """Main health check loop for a process."""
        start_time = datetime.now()
        start_period = healthcheck.get_start_period_seconds()
        interval = healthcheck.get_interval_seconds()
        timeout = healthcheck.get_timeout_seconds()
        retries = healthcheck.retries

        # Wait for start period
        if start_period > 0:
            await asyncio.sleep(start_period)

        # Update status to unknown (ready to check)
        if process_name in self._health_states:
            self._health_states[process_name].status = HealthStatus.UNKNOWN

        while True:
            try:
                # Run the health check command
                result = await self._local_context.exec_command(
                    healthcheck.test,
                    timeout=timeout,
                )

                state = self._health_states.get(process_name)
                if not state:
                    break

                state.last_check = datetime.now()
                state.check_count += 1
                old_status = state.status

                if result.exit_code == 0:
                    # Health check passed
                    state.consecutive_failures = 0
                    state.last_error = None
                    state.status = HealthStatus.HEALTHY
                else:
                    # Health check failed
                    state.consecutive_failures += 1
                    state.last_error = result.stderr or f"Exit code: {result.exit_code}"

                    if state.consecutive_failures >= retries:
                        state.status = HealthStatus.UNHEALTHY

                # Notify callbacks if status changed
                if old_status != state.status:
                    self._notify_status_change(process_name, state.status)

                # Wait for next interval
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log error but continue checking
                if process_name in self._health_states:
                    self._health_states[process_name].last_error = str(e)
                await asyncio.sleep(interval)

    def _notify_status_change(self, process_name: str, status: HealthStatus) -> None:
        """Notify all callbacks of a status change."""
        callbacks = self._callbacks.get(process_name, [])
        for callback in callbacks:
            try:
                callback(process_name, status)
            except Exception:
                pass  # Don't let callback errors break health checking

    async def run_single_check(
        self,
        process_name: str,
        healthcheck: HealthCheckDef,
    ) -> dict[str, Any]:
        """
        Run a single health check and return result.

        Useful for manual health check triggers.
        """
        timeout = healthcheck.get_timeout_seconds()

        result = await self._local_context.exec_command(
            healthcheck.test,
            timeout=timeout,
        )

        return {
            "success": result.exit_code == 0,
            "exit_code": result.exit_code,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "timestamp": datetime.now().isoformat(),
        }

    async def wait_for_healthy(
        self,
        process_name: str,
        healthcheck: HealthCheckDef,
        timeout: float = 60.0,
    ) -> bool:
        """
        Wait until a process becomes healthy or timeout.

        Args:
            process_name: Name of the process
            healthcheck: Health check definition
            timeout: Maximum time to wait in seconds

        Returns:
            True if healthy, False if timeout or unhealthy
        """
        start = datetime.now()
        check_interval = min(healthcheck.get_interval_seconds(), 1.0)

        while True:
            elapsed = (datetime.now() - start).total_seconds()
            if elapsed >= timeout:
                return False

            result = await self.run_single_check(process_name, healthcheck)
            if result["success"]:
                if process_name in self._health_states:
                    self._health_states[process_name].status = HealthStatus.HEALTHY
                return True

            await asyncio.sleep(check_interval)

    def to_dict(self, process_name: str) -> dict[str, Any]:
        """Get health state as a dictionary."""
        state = self.get_health(process_name)
        return {
            "status": state.status.value,
            "last_check": state.last_check.isoformat() if state.last_check else None,
            "consecutive_failures": state.consecutive_failures,
            "last_error": state.last_error,
            "check_count": state.check_count,
        }

    def reset(self) -> None:
        """Reset all health state (for testing)."""
        for task in self._check_tasks.values():
            task.cancel()
        self._check_tasks.clear()
        self._health_states.clear()
        self._callbacks.clear()


# Singleton
_health_checker: HealthChecker | None = None


def get_health_checker() -> HealthChecker:
    """Get the singleton HealthChecker instance."""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker


def reset_health_checker() -> None:
    """Reset the singleton (for testing)."""
    global _health_checker
    if _health_checker:
        _health_checker.reset()
    _health_checker = None
