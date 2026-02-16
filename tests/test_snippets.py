"""Tests for snippet management (Phase 5)."""

import json

from click.testing import CliRunner

from procler.cli import cli
from procler.core import get_snippet_manager


def test_snippet_list_empty():
    """Test listing snippets when none exist."""
    runner = CliRunner()

    result = runner.invoke(cli, ["snippet", "list"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["success"] is True
    assert data["data"]["snippets"] == []
    assert data["data"]["count"] == 0


def test_snippet_save():
    """Test saving a new snippet."""
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "snippet",
            "save",
            "--name",
            "hello-world",
            "--command",
            "echo hello",
            "--description",
            "Prints hello",
        ],
    )
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["success"] is True
    assert data["data"]["action"] == "created"
    assert data["data"]["snippet"]["name"] == "hello-world"
    assert data["data"]["snippet"]["command"] == "echo hello"
    assert data["data"]["snippet"]["description"] == "Prints hello"


def test_snippet_save_with_tags():
    """Test saving a snippet with tags."""
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "snippet",
            "save",
            "--name",
            "build-api",
            "--command",
            "docker compose build api",
            "--tags",
            "docker,build,api",
        ],
    )
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["success"] is True
    assert data["data"]["snippet"]["tags"] == ["docker", "build", "api"]


def test_snippet_list_with_snippets():
    """Test listing snippets after saving some."""
    runner = CliRunner()

    # Save two snippets
    runner.invoke(
        cli,
        [
            "snippet",
            "save",
            "--name",
            "snippet1",
            "--command",
            "echo 1",
        ],
    )
    runner.invoke(
        cli,
        [
            "snippet",
            "save",
            "--name",
            "snippet2",
            "--command",
            "echo 2",
        ],
    )

    # List all
    result = runner.invoke(cli, ["snippet", "list"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["success"] is True
    assert data["data"]["count"] == 2
    names = [s["name"] for s in data["data"]["snippets"]]
    assert "snippet1" in names
    assert "snippet2" in names


def test_snippet_list_with_tag_filter():
    """Test filtering snippets by tag."""
    runner = CliRunner()

    # Save snippets with different tags
    runner.invoke(
        cli,
        [
            "snippet",
            "save",
            "--name",
            "docker-build",
            "--command",
            "docker build .",
            "--tags",
            "docker,build",
        ],
    )
    runner.invoke(
        cli,
        [
            "snippet",
            "save",
            "--name",
            "npm-install",
            "--command",
            "npm install",
            "--tags",
            "npm,build",
        ],
    )
    runner.invoke(
        cli,
        [
            "snippet",
            "save",
            "--name",
            "docker-compose",
            "--command",
            "docker compose up",
            "--tags",
            "docker",
        ],
    )

    # Filter by 'docker' tag
    result = runner.invoke(cli, ["snippet", "list", "--tag", "docker"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["success"] is True
    assert data["data"]["count"] == 2
    names = [s["name"] for s in data["data"]["snippets"]]
    assert "docker-build" in names
    assert "docker-compose" in names
    assert "npm-install" not in names

    # Filter by 'build' tag
    result = runner.invoke(cli, ["snippet", "list", "--tag", "build"])
    data = json.loads(result.output)
    assert data["data"]["count"] == 2
    names = [s["name"] for s in data["data"]["snippets"]]
    assert "docker-build" in names
    assert "npm-install" in names


def test_snippet_run():
    """Test running a snippet."""
    runner = CliRunner()

    # Save a snippet
    runner.invoke(
        cli,
        [
            "snippet",
            "save",
            "--name",
            "test-echo",
            "--command",
            "echo hello world",
        ],
    )

    # Run it
    result = runner.invoke(cli, ["snippet", "run", "test-echo"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["success"] is True
    assert data["data"]["snippet"] == "test-echo"
    assert "hello world" in data["data"]["stdout"]
    assert data["data"]["exit_code"] == 0


def test_snippet_run_nonexistent():
    """Test running a snippet that doesn't exist."""
    runner = CliRunner()

    result = runner.invoke(cli, ["snippet", "run", "nonexistent"])
    assert result.exit_code == 1

    data = json.loads(result.output)
    assert data["success"] is False
    assert data["error_code"] == "snippet_not_found"


def test_snippet_remove():
    """Test removing a snippet."""
    runner = CliRunner()

    # Save a snippet
    runner.invoke(
        cli,
        [
            "snippet",
            "save",
            "--name",
            "to-remove",
            "--command",
            "echo test",
        ],
    )

    # Verify it exists
    list_result = runner.invoke(cli, ["snippet", "list"])
    assert json.loads(list_result.output)["data"]["count"] == 1

    # Remove it
    result = runner.invoke(cli, ["snippet", "remove", "to-remove"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["success"] is True
    assert data["data"]["action"] == "removed"
    assert data["data"]["name"] == "to-remove"

    # Verify it's gone
    list_result = runner.invoke(cli, ["snippet", "list"])
    assert json.loads(list_result.output)["data"]["count"] == 0


def test_snippet_remove_nonexistent():
    """Test removing a snippet that doesn't exist."""
    runner = CliRunner()

    result = runner.invoke(cli, ["snippet", "remove", "nonexistent"])
    assert result.exit_code == 1

    data = json.loads(result.output)
    assert data["success"] is False
    assert data["error_code"] == "snippet_not_found"


def test_snippet_save_duplicate():
    """Test saving a snippet with a name that already exists."""
    runner = CliRunner()

    # Save once
    runner.invoke(
        cli,
        [
            "snippet",
            "save",
            "--name",
            "duplicate",
            "--command",
            "echo test",
        ],
    )

    # Try to save again with same name
    result = runner.invoke(
        cli,
        [
            "snippet",
            "save",
            "--name",
            "duplicate",
            "--command",
            "echo different",
        ],
    )
    assert result.exit_code == 1

    data = json.loads(result.output)
    assert data["success"] is False
    assert data["error_code"] == "snippet_exists"


def test_snippet_docker_missing_container():
    """Test that docker snippet requires container name."""
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "snippet",
            "save",
            "--name",
            "docker-test",
            "--command",
            "ls",
            "--context",
            "docker",
            # Missing --container
        ],
    )
    assert result.exit_code == 1

    data = json.loads(result.output)
    assert data["success"] is False
    assert data["error_code"] == "missing_container"


def test_snippet_docker_with_container():
    """Test saving a docker snippet with container."""
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "snippet",
            "save",
            "--name",
            "docker-test",
            "--command",
            "ls -la",
            "--context",
            "docker",
            "--container",
            "my-container",
        ],
    )
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["success"] is True
    assert data["data"]["snippet"]["context_type"] == "docker"
    assert data["data"]["snippet"]["container_name"] == "my-container"


async def test_snippet_manager_directly():
    """Test SnippetManager methods directly."""
    manager = get_snippet_manager()

    # Save a snippet
    result = manager.save_snippet(
        name="direct-test",
        command="echo direct",
        description="Direct test",
        tags=["test"],
    )
    assert result["success"] is True

    # List snippets
    list_result = manager.list_snippets()
    assert list_result["data"]["count"] == 1

    # Filter by tag
    filtered = manager.list_snippets(tag="test")
    assert filtered["data"]["count"] == 1

    filtered = manager.list_snippets(tag="nonexistent")
    assert filtered["data"]["count"] == 0

    # Run snippet
    run_result = await manager.run_snippet("direct-test")
    assert run_result["success"] is True
    assert "direct" in run_result["data"]["stdout"]

    # Remove snippet
    remove_result = manager.remove_snippet("direct-test")
    assert remove_result["success"] is True

    # Verify gone
    final_list = manager.list_snippets()
    assert final_list["data"]["count"] == 0
