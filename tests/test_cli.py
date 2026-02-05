"""Tests for the CLI."""

import json
import tomllib
from pathlib import Path

from click.testing import CliRunner

from procler import __version__
from procler.cli import cli


def test_version():
    """Test --version flag outputs the package version and it matches pyproject.toml."""
    # Read source of truth from pyproject.toml
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        pyproject = tomllib.load(f)
    expected_version = pyproject["project"]["version"]

    # Verify __init__.py matches pyproject.toml
    assert __version__ == expected_version, (
        f"Version mismatch: __init__.py has {__version__}, " f"pyproject.toml has {expected_version}"
    )

    # Verify CLI output matches
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "procler" in result.output
    assert expected_version in result.output


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
