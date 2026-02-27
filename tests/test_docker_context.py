"""Tests for Docker context (Phase 4)."""

import json
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from procler.cli import cli


def test_docker_define_with_container():
    """Test defining a process with docker context."""
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "define",
            "--name",
            "docker-proc",
            "--command",
            "echo hello",
            "--context",
            "docker",
            "--container",
            "my-container",
        ],
    )
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["success"] is True
    assert data["data"]["action"] == "created"
    assert data["data"]["process"]["context_type"] == "docker"


def test_docker_define_missing_container():
    """Test that defining docker process without container fails."""
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "define",
            "--name",
            "docker-proc",
            "--command",
            "echo hello",
            "--context",
            "docker",
            # Missing --container
        ],
    )
    assert result.exit_code == 1

    data = json.loads(result.output)
    assert data["success"] is False
    assert data["error_code"] == "missing_container"


def test_docker_start_without_container_name():
    """Test starting docker process that was defined without container_name."""
    from sqler.query import SQLerField as F

    runner = CliRunner()

    # First define a local process
    runner.invoke(
        cli,
        [
            "define",
            "--name",
            "local-proc",
            "--command",
            "echo hello",
        ],
    )

    # Now manually modify it to be docker context without container
    # This simulates a corrupted database state
    from procler.db import init_database
    from procler.models import Process

    init_database()
    process = Process.query().filter(F("name") == "local-proc").all()[0]
    process.context_type = "docker"
    process.container_name = None  # No container name
    process.save()

    # Try to start it
    result = runner.invoke(cli, ["start", "local-proc"])
    assert result.exit_code == 1

    data = json.loads(result.output)
    assert data["success"] is False
    # Error depends on environment:
    # - docker_unavailable: Docker not installed/running
    # - missing_container: Docker available but no container specified
    assert data["error_code"] in ["missing_container", "docker_unavailable"]


def test_docker_exec_missing_container():
    """Test exec with docker context but no container."""
    runner = CliRunner()

    result = runner.invoke(
        cli,
        ["exec", "echo hello", "--context", "docker"],
    )
    assert result.exit_code == 1

    data = json.loads(result.output)
    assert data["success"] is False
    assert data["error_code"] == "missing_container"


def test_is_docker_available():
    """Test the is_docker_available function."""
    from procler.core import is_docker_available

    # Function should return a boolean
    result = is_docker_available()
    assert isinstance(result, bool)


# Tests with mocked Docker client
class TestDockerContextMocked:
    """Tests for DockerContext with mocked Docker client."""

    @patch("procler.core.context_docker.DOCKER_AVAILABLE", True)
    @patch("procler.core.context_docker.docker")
    def test_docker_context_initialization(self, mock_docker):
        """Test DockerContext can be initialized when Docker is available."""
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client

        from procler.core.context_docker import DockerContext

        context = DockerContext()
        assert context.context_type == "docker"
        mock_docker.from_env.assert_called_once()

    @patch("procler.core.context_docker.DOCKER_AVAILABLE", True)
    @patch("procler.core.context_docker.docker")
    def test_list_containers(self, mock_docker):
        """Test listing available containers."""
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_container.short_id = "abc123"
        mock_container.name = "test-container"
        mock_container.status = "running"
        mock_container.image.tags = ["python:3.12"]

        mock_client.containers.list.return_value = [mock_container]
        mock_docker.from_env.return_value = mock_client

        from procler.core.context_docker import DockerContext

        context = DockerContext()
        containers = context.list_containers()

        assert len(containers) == 1
        assert containers[0]["name"] == "test-container"
        assert containers[0]["status"] == "running"
        assert containers[0]["image"] == "python:3.12"

    @patch("procler.core.context_docker.DOCKER_AVAILABLE", True)
    @patch("procler.core.context_docker.docker")
    async def test_exec_command_success(self, mock_docker):
        """Test executing a command in a container."""
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_container.status = "running"
        mock_container.exec_run.return_value = (0, (b"hello\n", b""))

        mock_client.containers.get.return_value = mock_container
        mock_docker.from_env.return_value = mock_client

        from procler.core.context_docker import DockerContext

        context = DockerContext()
        result = await context.exec_command(
            command="echo hello",
            container_name="test-container",
        )

        assert result.exit_code == 0
        assert "hello" in result.stdout
        mock_container.exec_run.assert_called_once()

    @patch("procler.core.context_docker.DOCKER_AVAILABLE", True)
    @patch("procler.core.context_docker.docker")
    async def test_exec_command_container_not_running(self, mock_docker):
        """Test executing a command in a stopped container."""
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_container.status = "exited"

        mock_client.containers.get.return_value = mock_container
        mock_docker.from_env.return_value = mock_client

        from procler.core.context_docker import DockerContext

        context = DockerContext()
        result = await context.exec_command(
            command="echo hello",
            container_name="test-container",
        )

        assert result.exit_code == -1
        assert "not running" in result.stderr

    @patch("procler.core.context_docker.DOCKER_AVAILABLE", True)
    @patch("procler.core.context_docker.docker")
    async def test_exec_command_container_not_found(self, mock_docker):
        """Test executing a command when container doesn't exist."""
        from procler.core.context_docker import NotFound

        mock_client = MagicMock()
        mock_client.containers.get.side_effect = NotFound("Container not found")
        mock_docker.from_env.return_value = mock_client

        from procler.core.context_docker import DockerContext

        context = DockerContext()

        with pytest.raises(ValueError, match="not found"):
            await context.exec_command(
                command="echo hello",
                container_name="nonexistent",
            )
