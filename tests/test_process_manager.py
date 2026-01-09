"""Tests for process management."""

import json

from click.testing import CliRunner

from procler.cli import cli


def test_define_process():
    """Test defining a process via CLI."""
    runner = CliRunner()

    result = runner.invoke(
        cli,
        ["define", "--name", "test-proc", "--command", "echo hello"],
    )
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["success"] is True
    assert data["data"]["action"] == "created"
    assert data["data"]["process"]["name"] == "test-proc"


def test_start_process():
    """Test starting a process via CLI."""
    runner = CliRunner()

    # Define a process
    runner.invoke(
        cli,
        ["define", "--name", "test-proc", "--command", "sleep 10"],
    )

    # Start it
    result = runner.invoke(cli, ["start", "test-proc"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["success"] is True
    assert data["data"]["status"] == "started"
    assert data["data"]["process"]["status"] == "running"
    assert data["data"]["process"]["pid"] is not None

    # Clean up
    runner.invoke(cli, ["stop", "test-proc"])


def test_stop_process():
    """Test stopping a process via CLI."""
    runner = CliRunner()

    # Define and start
    runner.invoke(
        cli,
        ["define", "--name", "test-proc", "--command", "sleep 30"],
    )
    runner.invoke(cli, ["start", "test-proc"])

    # Stop it
    result = runner.invoke(cli, ["stop", "test-proc"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["success"] is True
    assert data["data"]["status"] == "stopped"


def test_restart_process():
    """Test restarting a process via CLI."""
    runner = CliRunner()

    # Define and start
    runner.invoke(
        cli,
        ["define", "--name", "test-proc", "--command", "sleep 30"],
    )
    runner.invoke(cli, ["start", "test-proc"])

    # Restart it
    result = runner.invoke(cli, ["restart", "test-proc"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["success"] is True
    assert data["data"]["status"] == "started"
    assert data["data"]["process"]["status"] == "running"

    # Clean up
    runner.invoke(cli, ["stop", "test-proc"])


def test_start_already_running():
    """Test that starting an already running process is idempotent."""
    runner = CliRunner()

    # Define and start
    runner.invoke(
        cli,
        ["define", "--name", "test-proc", "--command", "sleep 30"],
    )
    start_result = runner.invoke(cli, ["start", "test-proc"])
    first_pid = json.loads(start_result.output)["data"]["process"]["pid"]

    # Start again - should be idempotent
    result = runner.invoke(cli, ["start", "test-proc"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["success"] is True
    assert data["data"]["status"] == "already_running"
    assert data["data"]["process"]["pid"] == first_pid

    # Clean up
    runner.invoke(cli, ["stop", "test-proc"])


def test_stop_already_stopped():
    """Test that stopping an already stopped process is idempotent."""
    runner = CliRunner()

    # Define (but don't start)
    runner.invoke(
        cli,
        ["define", "--name", "test-proc", "--command", "sleep 30"],
    )

    # Stop it (should be idempotent)
    result = runner.invoke(cli, ["stop", "test-proc"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["success"] is True
    assert data["data"]["status"] == "already_stopped"


def test_status_running_process():
    """Test status shows running process with uptime."""
    runner = CliRunner()

    # Define and start
    runner.invoke(
        cli,
        ["define", "--name", "test-proc", "--command", "sleep 30"],
    )
    runner.invoke(cli, ["start", "test-proc"])

    # Check status
    result = runner.invoke(cli, ["status", "test-proc"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["success"] is True
    assert data["data"]["process"]["status"] == "running"
    assert data["data"]["process"]["pid"] is not None

    # Clean up
    runner.invoke(cli, ["stop", "test-proc"])


def test_start_nonexistent_process():
    """Test starting a process that doesn't exist."""
    runner = CliRunner()

    result = runner.invoke(cli, ["start", "nonexistent"])
    assert result.exit_code == 1

    data = json.loads(result.output)
    assert data["success"] is False
    assert data["error_code"] == "process_not_found"


def test_stop_nonexistent_process():
    """Test stopping a process that doesn't exist."""
    runner = CliRunner()

    result = runner.invoke(cli, ["stop", "nonexistent"])
    assert result.exit_code == 1

    data = json.loads(result.output)
    assert data["success"] is False
    assert data["error_code"] == "process_not_found"
