"""Tests for the CLI."""

import json

from click.testing import CliRunner

from procler.cli import cli


def test_version():
    """Test --version flag."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "procler" in result.output
    assert "0.1.0" in result.output


def test_capabilities():
    """Test capabilities command returns valid JSON schema."""
    runner = CliRunner()
    result = runner.invoke(cli, ["capabilities"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["success"] is True
    assert "data" in data
    assert data["data"]["name"] == "procler"
    assert "commands" in data["data"]
    assert "status" in data["data"]["commands"]
    assert "start" in data["data"]["commands"]
    assert "stop" in data["data"]["commands"]
    assert "define" in data["data"]["commands"]


def test_status_empty():
    """Test status with no processes defined."""
    runner = CliRunner()
    result = runner.invoke(cli, ["status"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["success"] is True
    assert data["data"]["processes"] == []


def test_list_empty():
    """Test list with no processes defined."""
    runner = CliRunner()
    result = runner.invoke(cli, ["list"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["success"] is True
    assert data["data"]["processes"] == []
