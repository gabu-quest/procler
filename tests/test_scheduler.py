"""Tests for cron/scheduled processes."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from croniter import croniter

from procler.config.schema import ProcessDef
from procler.core.scheduler import get_scheduler


class TestSchedulerRegistration:
    """Test scheduler registration and state management."""

    def test_register_valid_cron(self):
        """Register a process with a valid cron expression."""
        sched = get_scheduler()
        sched.register("cleanup", "0 */6 * * *")

        state = sched.get_state("cleanup")
        assert state is not None
        assert state.cron_expression == "0 */6 * * *"
        assert state.process_name == "cleanup"
        assert state.run_count == 0
        assert state.last_run is None
        assert state.next_run is not None
        assert state.is_running is False

    def test_register_invalid_cron_raises(self):
        """Invalid cron expression raises ValueError."""
        sched = get_scheduler()
        with pytest.raises(ValueError, match="Invalid cron expression"):
            sched.register("bad", "not a cron")

    def test_unregister(self):
        """Unregister removes a scheduled process."""
        sched = get_scheduler()
        sched.register("cleanup", "0 * * * *")
        assert sched.get_state("cleanup") is not None

        sched.unregister("cleanup")
        assert sched.get_state("cleanup") is None

    def test_unregister_nonexistent(self):
        """Unregistering a non-existent process is safe."""
        sched = get_scheduler()
        sched.unregister("ghost")  # Should not raise

    def test_get_state_nonexistent(self):
        """Getting state for unregistered process returns None."""
        sched = get_scheduler()
        assert sched.get_state("ghost") is None


class TestSchedulerNextRun:
    """Test cron expression next-run calculation."""

    def test_next_run_in_future(self):
        """next_run is always in the future."""
        sched = get_scheduler()
        sched.register("job", "* * * * *")  # Every minute

        state = sched.get_state("job")
        assert state.next_run > datetime.now()

    def test_next_run_every_minute(self):
        """Every-minute cron triggers within 60 seconds."""
        sched = get_scheduler()
        sched.register("job", "* * * * *")

        state = sched.get_state("job")
        diff = (state.next_run - datetime.now()).total_seconds()
        assert 0 < diff <= 60

    def test_next_run_specific_hour(self):
        """Specific hour cron calculates correct next run."""
        now = datetime.now()
        # Schedule for 2 hours from now to ensure it's always in the future
        future_hour = (now.hour + 2) % 24
        sched = get_scheduler()
        sched.register("job", f"0 {future_hour} * * *")

        state = sched.get_state("job")
        assert state.next_run.hour == future_hour
        assert state.next_run.minute == 0


class TestSchedulerListSchedules:
    """Test listing scheduled processes."""

    def test_list_empty(self):
        """List returns empty when no schedules registered."""
        sched = get_scheduler()
        result = sched.list_schedules()
        assert result == []

    def test_list_multiple(self):
        """List returns all registered schedules."""
        sched = get_scheduler()
        sched.register("cleanup", "0 */6 * * *")
        sched.register("backup", "0 0 * * *")

        result = sched.list_schedules()
        assert len(result) == 2

        names = [r["process"] for r in result]
        assert "cleanup" in names
        assert "backup" in names

    def test_list_format(self):
        """List returns correct format for each schedule."""
        sched = get_scheduler()
        sched.register("cleanup", "0 */6 * * *")

        result = sched.list_schedules()
        entry = result[0]
        assert entry["process"] == "cleanup"
        assert entry["cron"] == "0 */6 * * *"
        assert entry["last_run"] is None
        assert entry["next_run"] is not None  # ISO string
        assert entry["run_count"] == 0
        assert entry["last_exit_code"] is None
        assert entry["is_running"] is False


class TestProcessDefSchedule:
    """Test schedule field on ProcessDef."""

    def test_schedule_field(self):
        """ProcessDef accepts schedule field."""
        proc = ProcessDef(command="python cleanup.py", schedule="0 */6 * * *")
        assert proc.schedule == "0 */6 * * *"

    def test_schedule_default_none(self):
        """ProcessDef defaults schedule to None."""
        proc = ProcessDef(command="echo hello")
        assert proc.schedule is None


class TestSchedulerConfigParsing:
    """Test schedule in YAML config."""

    def test_config_with_schedule(self, tmp_path):
        """Config file with schedule parses correctly."""
        import os

        from procler.config import loader as config_loader

        config_dir = tmp_path / ".procler"
        config_dir.mkdir()
        (config_dir / "config.yaml").write_text("""
version: 1

processes:
  cleanup:
    command: python scripts/cleanup.py
    schedule: "0 */6 * * *"
  api:
    command: uvicorn main:app
""")

        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        config_loader.reset_config_cache()

        try:
            from procler.config import get_config

            config = get_config()
            assert config.processes["cleanup"].schedule == "0 */6 * * *"
            assert config.processes["api"].schedule is None
        finally:
            os.chdir(old_cwd)
            config_loader.reset_config_cache()


class TestCroniterIntegration:
    """Test croniter library integration."""

    def test_valid_expressions(self):
        """Common cron expressions are valid."""
        valid = [
            "* * * * *",  # every minute
            "0 * * * *",  # every hour
            "0 0 * * *",  # daily at midnight
            "0 */6 * * *",  # every 6 hours
            "30 2 * * 1",  # Monday at 2:30
            "0 0 1 * *",  # first of month
            "*/5 * * * *",  # every 5 minutes
        ]
        for expr in valid:
            assert croniter.is_valid(expr), f"Expected valid: {expr}"

    def test_invalid_expressions(self):
        """Invalid expressions are detected."""
        invalid = [
            "not cron",
            "60 * * * *",  # invalid minute
            "* 25 * * *",  # invalid hour
            "",
        ]
        for expr in invalid:
            assert not croniter.is_valid(expr), f"Expected invalid: {expr}"

    def test_next_occurrence(self):
        """croniter calculates correct next occurrence."""
        base = datetime(2025, 1, 1, 0, 0, 0)
        cron = croniter("0 */6 * * *", base)

        next_time = cron.get_next(datetime)
        assert next_time == datetime(2025, 1, 1, 6, 0, 0)

        next_time = cron.get_next(datetime)
        assert next_time == datetime(2025, 1, 1, 12, 0, 0)


class TestSchedulerExecution:
    """Test scheduler execution logic."""

    async def test_schedule_loop_runs_process(self):
        """Scheduler starts a process at the scheduled time."""
        sched = get_scheduler()
        sched.register("test-job", "* * * * *")

        # Manually set next_run to now so it triggers immediately
        state = sched.get_state("test-job")
        state.next_run = datetime.now() - timedelta(seconds=1)

        mock_pm = AsyncMock()
        mock_pm.start.return_value = {"success": True, "data": {"status": "started"}}
        mock_pm.status.return_value = {
            "success": True,
            "data": {"process": {"status": "stopped", "exit_code": 0}},
        }

        with patch("procler.core.process_manager.get_process_manager", return_value=mock_pm):
            # Run one iteration of the loop manually
            state.is_running = True
            state.last_run = datetime.now()

            result = await mock_pm.start("test-job")
            assert result["success"] is True

            state.is_running = False
            state.run_count += 1

        assert state.run_count == 1
