"""Tests for logs and exec commands (Phase 3)."""

import asyncio
import json
import time

from click.testing import CliRunner

from procgler.cli import cli
from procgler.core import get_process_manager
from procgler.models import LogEntry


def test_logs_empty():
    """Test getting logs for a process with no log entries."""
    runner = CliRunner()

    # Define a process (but don't start it)
    runner.invoke(
        cli,
        ["define", "--name", "test-proc", "--command", "echo hello"],
    )

    # Get logs
    result = runner.invoke(cli, ["logs", "test-proc"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["success"] is True
    assert data["data"]["process"] == "test-proc"
    assert data["data"]["logs"] == []
    assert data["data"]["count"] == 0


async def test_logs_with_output():
    """Test getting logs for a process that has generated output."""
    from procgler.db import init_database
    from procgler.models import Process
    from datetime import datetime

    init_database()

    # Create a process and add log entries directly
    process = Process(
        name="test-logs-output",
        command="echo hello",
        created_at=datetime.now().isoformat(),
    )
    process.save()

    # Add log entries
    for i, line in enumerate(["line1", "line2", "line3"]):
        LogEntry(
            process_id=process._id,
            stream="stdout",
            line=line,
            timestamp=datetime.now().isoformat(),
        ).save()

    # Get logs via ProcessManager
    manager = get_process_manager()
    result = await manager.logs("test-logs-output")

    assert result["success"] is True
    assert result["data"]["count"] == 3
    log_lines = [log["line"] for log in result["data"]["logs"]]
    assert "line1" in log_lines
    assert "line2" in log_lines
    assert "line3" in log_lines


async def test_logs_with_tail():
    """Test getting logs with --tail option."""
    from procgler.db import init_database
    from procgler.models import Process
    from datetime import datetime

    init_database()

    # Create a process
    process = Process(
        name="test-logs-tail",
        command="seq 1 10",
        created_at=datetime.now().isoformat(),
    )
    process.save()

    # Add 10 log entries
    for i in range(10):
        LogEntry(
            process_id=process._id,
            stream="stdout",
            line=str(i + 1),
            timestamp=datetime.now().isoformat(),
        ).save()
        time.sleep(0.01)  # Ensure different timestamps

    # Get only last 3 lines
    manager = get_process_manager()
    result = await manager.logs("test-logs-tail", tail=3)

    assert result["success"] is True
    assert result["data"]["count"] == 3

    # Should have the last 3 entries (8, 9, 10)
    log_lines = [log["line"] for log in result["data"]["logs"]]
    assert "8" in log_lines
    assert "9" in log_lines
    assert "10" in log_lines


def test_logs_nonexistent_process():
    """Test getting logs for a process that doesn't exist."""
    runner = CliRunner()

    result = runner.invoke(cli, ["logs", "nonexistent"])
    assert result.exit_code == 1

    data = json.loads(result.output)
    assert data["success"] is False
    assert data["error_code"] == "process_not_found"


def test_exec_simple_command():
    """Test executing a simple command."""
    runner = CliRunner()

    result = runner.invoke(cli, ["exec", "echo hello"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["success"] is True
    assert "hello" in data["data"]["stdout"]
    assert data["data"]["exit_code"] == 0


def test_exec_with_cwd():
    """Test executing a command with working directory."""
    runner = CliRunner()

    result = runner.invoke(cli, ["exec", "pwd", "--cwd", "/tmp"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["success"] is True
    assert "/tmp" in data["data"]["stdout"]
    assert data["data"]["exit_code"] == 0


def test_exec_command_with_stderr():
    """Test executing a command that writes to stderr."""
    runner = CliRunner()

    result = runner.invoke(cli, ["exec", "ls /nonexistent_dir"])
    # ls returns non-zero for non-existent directory
    assert result.exit_code == 0  # CLI succeeds, but command fails

    data = json.loads(result.output)
    assert data["success"] is True
    assert data["data"]["exit_code"] != 0
    assert len(data["data"]["stderr"]) > 0


def test_exec_command_exit_code():
    """Test that exec returns the correct exit code."""
    runner = CliRunner()

    result = runner.invoke(cli, ["exec", "exit 42"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["success"] is True
    assert data["data"]["exit_code"] == 42


def test_exec_docker_unavailable():
    """Test that docker context returns unavailable when Docker is not running."""
    runner = CliRunner()

    result = runner.invoke(
        cli,
        ["exec", "echo hello", "--context", "docker", "--container", "test"],
    )
    assert result.exit_code == 1

    data = json.loads(result.output)
    assert data["success"] is False
    # When Docker is not available, we get docker_unavailable
    # When Docker is available but container doesn't exist, we get container_not_found
    assert data["error_code"] in ["docker_unavailable", "container_not_found"]


def test_exec_docker_missing_container():
    """Test that docker context requires container name."""
    runner = CliRunner()

    result = runner.invoke(
        cli,
        ["exec", "echo hello", "--context", "docker"],
    )
    assert result.exit_code == 1

    data = json.loads(result.output)
    assert data["success"] is False
    assert data["error_code"] == "missing_container"


async def test_log_rotation():
    """Test log rotation functionality."""
    from procgler.db import init_database
    from procgler.models import Process
    from datetime import datetime

    init_database()

    # Create a process
    process = Process(
        name="test-rotation",
        command="echo hello",
        created_at=datetime.now().isoformat(),
    )
    process.save()

    # Create many log entries
    for i in range(20):
        log = LogEntry(
            process_id=process._id,
            stream="stdout",
            line=f"line {i}",
            timestamp=datetime.now().isoformat(),
        )
        log.save()

    # Verify we have 20 logs
    all_logs = LogEntry.query().all()
    process_logs = [log for log in all_logs if log.process_id == process._id]
    assert len(process_logs) == 20

    # Rotate logs to keep only 5
    manager = get_process_manager()
    deleted = manager.rotate_logs(process._id, max_entries=5)
    assert deleted == 15

    # Verify we now have only 5 logs
    all_logs = LogEntry.query().all()
    process_logs = [log for log in all_logs if log.process_id == process._id]
    assert len(process_logs) == 5


async def test_cleanup_all_logs():
    """Test cleanup_all_logs functionality."""
    from procgler.db import init_database
    from procgler.models import Process
    from datetime import datetime

    init_database()

    # Create two processes
    process1 = Process(
        name="test-cleanup-1",
        command="echo hello",
        created_at=datetime.now().isoformat(),
    )
    process1.save()

    process2 = Process(
        name="test-cleanup-2",
        command="echo hello",
        created_at=datetime.now().isoformat(),
    )
    process2.save()

    # Create logs for both processes
    for i in range(15):
        LogEntry(
            process_id=process1._id,
            stream="stdout",
            line=f"line {i}",
            timestamp=datetime.now().isoformat(),
        ).save()

    for i in range(8):
        LogEntry(
            process_id=process2._id,
            stream="stdout",
            line=f"line {i}",
            timestamp=datetime.now().isoformat(),
        ).save()

    # Cleanup all logs with max 10 per process
    manager = get_process_manager()
    results = manager.cleanup_all_logs(max_entries_per_process=10)

    # Only process1 should have deletions (15 - 10 = 5)
    assert "test-cleanup-1" in results
    assert results["test-cleanup-1"] == 5
    # process2 only has 8 logs, no deletions
    assert "test-cleanup-2" not in results
