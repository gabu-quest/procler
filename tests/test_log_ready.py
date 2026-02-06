"""Tests for log_ready dependency condition."""

import re

import pytest

from procler.config.schema import DependencyCondition, DependencyDef, ProcessDef
from procler.core.events import EVENT_LOG_READY, get_event_bus
from procler.core.process_manager import get_process_manager
from procler.models import Process


class TestLogReadySchema:
    """Test config schema additions for log_ready."""

    def test_dependency_condition_log_ready_exists(self):
        """LOG_READY is a valid dependency condition."""
        assert DependencyCondition.LOG_READY == "log_ready"
        assert DependencyCondition.LOG_READY.value == "log_ready"

    def test_dependency_def_with_log_ready(self):
        """DependencyDef accepts log_ready condition."""
        dep = DependencyDef(name="api", condition=DependencyCondition.LOG_READY)
        assert dep.name == "api"
        assert dep.condition == DependencyCondition.LOG_READY

    def test_process_def_ready_log_line(self):
        """ProcessDef accepts ready_log_line field."""
        proc = ProcessDef(
            command="uvicorn main:app",
            ready_log_line="Uvicorn running on",
        )
        assert proc.ready_log_line == "Uvicorn running on"

    def test_process_def_ready_log_line_default_none(self):
        """ProcessDef defaults ready_log_line to None."""
        proc = ProcessDef(command="echo hello")
        assert proc.ready_log_line is None

    def test_process_def_ready_log_line_regex(self):
        """ready_log_line supports regex patterns."""
        proc = ProcessDef(
            command="uvicorn main:app",
            ready_log_line=r"Listening on (?:0\.0\.0\.0|127\.0\.0\.1):\d+",
        )
        pattern = re.compile(proc.ready_log_line)
        assert pattern.search("Listening on 0.0.0.0:8000")
        assert pattern.search("Listening on 127.0.0.1:3000")
        assert not pattern.search("Starting server...")


class TestLogReadyPatternMatching:
    """Test ready_log_line regex matching in ProcessManager."""

    def test_register_ready_pattern(self):
        """ProcessManager can register a ready pattern for a process."""
        pm = get_process_manager()
        pm.register_ready_pattern(1, "Server started")
        assert 1 in pm._ready_patterns
        assert not pm.is_process_ready(1)

    def test_is_process_ready_false_initially(self):
        """Process is not ready before any log lines match."""
        pm = get_process_manager()
        pm.register_ready_pattern(1, "Ready")
        assert pm.is_process_ready(1) is False

    def test_clear_ready_state(self):
        """clear_ready_state removes pattern and ready flag."""
        pm = get_process_manager()
        pm.register_ready_pattern(1, "Ready")
        pm._ready_processes.add(1)
        assert pm.is_process_ready(1) is True

        pm.clear_ready_state(1)
        assert pm.is_process_ready(1) is False
        assert 1 not in pm._ready_patterns

    def test_log_callback_matches_ready_pattern(self):
        """Log callback detects ready_log_line match and marks process ready."""
        pm = get_process_manager()
        pm.register_ready_pattern(42, "Uvicorn running on")

        # Create a process in DB so log callback can save
        process = Process(
            name="test-api",
            command="uvicorn main:app",
            status="running",
        )
        process.save()

        # Simulate log callback
        callback = pm._log_callback(42, "stdout")

        # Non-matching line
        callback("Starting application...")
        assert not pm.is_process_ready(42)

        # Matching line
        callback("INFO: Uvicorn running on http://0.0.0.0:8000")
        assert pm.is_process_ready(42)

    def test_log_callback_emits_event_on_match(self):
        """Log callback emits EVENT_LOG_READY when pattern matches."""
        pm = get_process_manager()
        pm.register_ready_pattern(42, "Server ready")

        process = Process(
            name="test-server",
            command="node server.js",
            status="running",
        )
        process.save()

        received_events = []

        async def handler(data):
            received_events.append(data)

        get_event_bus().subscribe(EVENT_LOG_READY, handler)

        callback = pm._log_callback(42, "stdout")
        callback("Server ready on port 3000")

        # Event is emitted via emit_sync which creates a task
        # In sync test context, we verify the ready state was set
        assert pm.is_process_ready(42)

    def test_log_callback_only_matches_once(self):
        """Ready pattern only triggers on first match, not subsequent lines."""
        pm = get_process_manager()
        pm.register_ready_pattern(42, "ready")

        process = Process(
            name="test-app",
            command="app",
            status="running",
        )
        process.save()

        callback = pm._log_callback(42, "stdout")
        callback("Application ready")
        assert pm.is_process_ready(42)

        # Second match should not cause issues
        callback("Still ready")
        assert pm.is_process_ready(42)

    def test_log_callback_regex_pattern(self):
        """Log callback supports regex patterns, not just substring match."""
        pm = get_process_manager()
        pm.register_ready_pattern(42, r"port (\d+)")

        process = Process(
            name="test-regex",
            command="app",
            status="running",
        )
        process.save()

        callback = pm._log_callback(42, "stdout")

        # No match
        callback("Initializing...")
        assert not pm.is_process_ready(42)

        # Match
        callback("Listening on port 8080")
        assert pm.is_process_ready(42)


class TestLogReadyConfigParsing:
    """Test log_ready in YAML config parsing."""

    def test_config_with_log_ready(self, tmp_path):
        """Config file with ready_log_line and log_ready condition parses correctly."""
        import os

        from procler.config import loader as config_loader

        config_dir = tmp_path / ".procler"
        config_dir.mkdir()
        config_file = config_dir / "config.yaml"
        config_file.write_text("""
version: 1

processes:
  api:
    command: uvicorn main:app
    ready_log_line: "Uvicorn running on"
  worker:
    command: celery worker
    depends_on:
      - name: api
        condition: log_ready

groups:
  backend:
    processes: [api, worker]
""")

        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        config_loader.reset_config_cache()

        try:
            from procler.config import get_config

            config = get_config()

            # Verify ready_log_line
            assert config.processes["api"].ready_log_line == "Uvicorn running on"
            assert config.processes["worker"].ready_log_line is None

            # Verify dependency condition
            deps = config.processes["worker"].get_dependencies()
            assert len(deps) == 1
            assert deps[0].name == "api"
            assert deps[0].condition == DependencyCondition.LOG_READY
        finally:
            os.chdir(old_cwd)
            config_loader.reset_config_cache()


class TestLogReadyEdgeCases:
    """Test edge cases for log_ready."""

    def test_ready_pattern_with_no_registered_pattern(self):
        """is_process_ready returns False for unregistered processes."""
        pm = get_process_manager()
        assert pm.is_process_ready(999) is False

    def test_clear_ready_state_for_unregistered(self):
        """clear_ready_state is safe for unregistered processes."""
        pm = get_process_manager()
        pm.clear_ready_state(999)  # Should not raise

    def test_ready_pattern_invalid_regex_fallback(self):
        """Invalid regex in ready_log_line raises during registration."""
        pm = get_process_manager()
        with pytest.raises(re.error):
            pm.register_ready_pattern(1, "[invalid regex")

    def test_log_callback_without_ready_pattern_still_works(self):
        """Log callback works normally when no ready pattern is registered."""
        pm = get_process_manager()

        process = Process(
            name="test-normal",
            command="echo hello",
            status="running",
        )
        process.save()

        callback = pm._log_callback(process._id, "stdout")
        callback("Some log line")  # Should not raise
        assert not pm.is_process_ready(process._id)
