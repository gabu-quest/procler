"""Cron-based process scheduler."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from croniter import croniter

logger = logging.getLogger(__name__)


@dataclass
class ScheduleState:
    """State for a scheduled process."""

    cron_expression: str
    process_name: str
    last_run: datetime | None = None
    next_run: datetime | None = None
    run_count: int = 0
    last_exit_code: int | None = None
    is_running: bool = False


class Scheduler:
    """Manages cron-scheduled process execution.

    Processes with a `schedule` field are run on a cron schedule
    rather than being long-running daemons.
    """

    def __init__(self):
        self._schedules: dict[str, ScheduleState] = {}  # process_name -> state
        self._tasks: dict[str, asyncio.Task] = {}  # process_name -> background task

    def register(self, process_name: str, cron_expression: str) -> None:
        """Register a process for scheduled execution.

        Args:
            process_name: Name of the process to schedule
            cron_expression: Cron expression (e.g., "0 */6 * * *")

        Raises:
            ValueError: If the cron expression is invalid
        """
        if not croniter.is_valid(cron_expression):
            raise ValueError(f"Invalid cron expression: {cron_expression}")

        now = datetime.now()
        cron = croniter(cron_expression, now)
        next_run = cron.get_next(datetime)

        self._schedules[process_name] = ScheduleState(
            cron_expression=cron_expression,
            process_name=process_name,
            next_run=next_run,
        )

    def unregister(self, process_name: str) -> None:
        """Remove a process from the schedule."""
        self._schedules.pop(process_name, None)
        task = self._tasks.pop(process_name, None)
        if task and not task.done():
            task.cancel()

    def get_state(self, process_name: str) -> ScheduleState | None:
        """Get the schedule state for a process."""
        return self._schedules.get(process_name)

    def list_schedules(self) -> list[dict[str, Any]]:
        """List all registered schedules."""
        result = []
        for name, state in self._schedules.items():
            result.append(
                {
                    "process": name,
                    "cron": state.cron_expression,
                    "last_run": state.last_run.isoformat() if state.last_run else None,
                    "next_run": state.next_run.isoformat() if state.next_run else None,
                    "run_count": state.run_count,
                    "last_exit_code": state.last_exit_code,
                    "is_running": state.is_running,
                }
            )
        return result

    async def start(self) -> None:
        """Start the scheduler loop for all registered processes."""
        for process_name in self._schedules:
            if process_name not in self._tasks or self._tasks[process_name].done():
                self._tasks[process_name] = asyncio.create_task(self._schedule_loop(process_name))

    async def stop(self) -> None:
        """Stop all scheduler loops."""
        for task in self._tasks.values():
            if not task.done():
                task.cancel()
        for task in self._tasks.values():
            try:
                await task
            except asyncio.CancelledError:
                pass
        self._tasks.clear()

    async def _schedule_loop(self, process_name: str) -> None:
        """Background loop that runs a process on its cron schedule."""
        while True:
            try:
                state = self._schedules.get(process_name)
                if not state or not state.next_run:
                    break

                # Calculate seconds until next run
                now = datetime.now()
                wait_seconds = (state.next_run - now).total_seconds()

                if wait_seconds > 0:
                    await asyncio.sleep(wait_seconds)

                # Time to run
                state.is_running = True
                state.last_run = datetime.now()

                try:
                    from .process_manager import get_process_manager

                    pm = get_process_manager()
                    result = await pm.start(process_name)

                    if result.get("success"):
                        # Wait for the process to complete (it's a one-shot, not a daemon)
                        exit_code = await self._wait_for_completion(process_name, timeout=3600)
                        state.last_exit_code = exit_code
                    else:
                        logger.error(f"Failed to start scheduled process '{process_name}': {result.get('error')}")
                        state.last_exit_code = -1

                except Exception as e:
                    logger.error(f"Error running scheduled process '{process_name}': {e}")
                    state.last_exit_code = -1
                finally:
                    state.is_running = False
                    state.run_count += 1

                # Calculate next run
                cron = croniter(state.cron_expression, datetime.now())
                state.next_run = cron.get_next(datetime)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler loop error for '{process_name}': {e}")
                await asyncio.sleep(60)  # Back off on error

    async def _wait_for_completion(self, process_name: str, timeout: float = 3600) -> int:
        """Wait for a scheduled process to complete.

        Returns the exit code (0 for success, non-zero for failure).
        """
        from .process_manager import get_process_manager

        pm = get_process_manager()
        start = datetime.now()

        while True:
            elapsed = (datetime.now() - start).total_seconds()
            if elapsed >= timeout:
                logger.warning(f"Scheduled process '{process_name}' timed out after {timeout}s")
                await pm.stop(process_name)
                return -1

            status = await pm.status(process_name)
            if status.get("success"):
                proc_status = status.get("data", {}).get("process", {}).get("status")
                if proc_status == "stopped":
                    exit_code = status.get("data", {}).get("process", {}).get("exit_code")
                    return exit_code if exit_code is not None else 0
                elif proc_status == "error":
                    return -1

            await asyncio.sleep(1)

    def reset(self) -> None:
        """Reset all schedules (for testing)."""
        for task in self._tasks.values():
            if not task.done():
                task.cancel()
        self._tasks.clear()
        self._schedules.clear()


# Singleton
_scheduler: Scheduler | None = None


def get_scheduler() -> Scheduler:
    """Get the singleton Scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = Scheduler()
    return _scheduler


def reset_scheduler() -> None:
    """Reset the singleton (for testing)."""
    global _scheduler
    if _scheduler:
        _scheduler.reset()
    _scheduler = None
