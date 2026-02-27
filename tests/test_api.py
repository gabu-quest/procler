"""Tests for FastAPI endpoints (Phase 6)."""

import pytest
from fastapi.testclient import TestClient

from procler.api import create_app
from procler.api.app import lifespan


@pytest.fixture
def client():
    """Create a test client for the API."""
    app = create_app()
    return TestClient(app)


def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


async def test_lifespan_startup_shutdown():
    """Test that lifespan context manager starts and shuts down cleanly."""
    from unittest.mock import MagicMock

    # Create a mock app
    app = MagicMock()

    # Test that lifespan can be entered and exited without errors
    async with lifespan(app):
        # Verify startup initialized the event bus
        from procler.core.events import get_event_bus

        bus = get_event_bus()
        assert bus is not None

    # If we exit cleanly, shutdown succeeded


# Process endpoints tests


def test_list_processes_empty(client):
    """Test listing processes when none exist."""
    response = client.get("/api/processes")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["processes"] == []


def test_create_process(client):
    """Test creating a process via API."""
    response = client.post(
        "/api/processes",
        json={
            "name": "test-api-process",
            "command": "echo hello",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["action"] == "created"
    assert data["data"]["process"]["name"] == "test-api-process"


def test_create_process_with_tags(client):
    """Test creating a process with tags."""
    response = client.post(
        "/api/processes",
        json={
            "name": "tagged-process",
            "command": "sleep 10",
            "tags": ["test", "api"],
            "display_name": "Tagged Process",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_create_process_docker_missing_container(client):
    """Test that docker process requires container name."""
    response = client.post(
        "/api/processes",
        json={
            "name": "docker-process",
            "command": "ls",
            "context_type": "docker",
        },
    )
    assert response.status_code == 200  # Returns 200 with error in body
    data = response.json()
    assert data["success"] is False
    assert data["error_code"] == "missing_container"


def test_create_process_duplicate(client):
    """Test creating a process with duplicate name."""
    # Create first
    client.post(
        "/api/processes",
        json={
            "name": "duplicate-test",
            "command": "echo test",
        },
    )

    # Try to create again
    response = client.post(
        "/api/processes",
        json={
            "name": "duplicate-test",
            "command": "echo different",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["error_code"] == "process_exists"


def test_get_process(client):
    """Test getting a specific process."""
    # Create a process first
    client.post(
        "/api/processes",
        json={
            "name": "get-test",
            "command": "echo hello",
        },
    )

    response = client.get("/api/processes/get-test")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["process"]["name"] == "get-test"


def test_get_process_not_found(client):
    """Test getting a process that doesn't exist."""
    response = client.get("/api/processes/nonexistent")
    assert response.status_code == 404


def test_delete_process(client):
    """Test deleting a process."""
    # Create a process first
    client.post(
        "/api/processes",
        json={
            "name": "delete-test",
            "command": "echo hello",
        },
    )

    response = client.delete("/api/processes/delete-test")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["action"] == "removed"

    # Verify it's gone
    response = client.get("/api/processes/delete-test")
    assert response.status_code == 404


def test_delete_process_not_found(client):
    """Test deleting a process that doesn't exist."""
    response = client.delete("/api/processes/nonexistent")
    assert response.status_code == 404


def test_start_process(client):
    """Test starting a process via API."""
    # Create a process
    client.post(
        "/api/processes",
        json={
            "name": "start-test",
            "command": "sleep 30",
        },
    )

    # Start it
    response = client.post("/api/processes/start-test/start")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "started"

    # Clean up
    client.post("/api/processes/start-test/stop")


def test_stop_process(client):
    """Test stopping a process via API."""
    # Create and start a process
    client.post(
        "/api/processes",
        json={
            "name": "stop-test",
            "command": "sleep 30",
        },
    )
    client.post("/api/processes/stop-test/start")

    # Stop it
    response = client.post("/api/processes/stop-test/stop")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "stopped"


def test_restart_process(client):
    """Test restarting a process via API."""
    # Create and start a process
    client.post(
        "/api/processes",
        json={
            "name": "restart-test",
            "command": "sleep 30",
        },
    )
    client.post("/api/processes/restart-test/start")

    # Restart it
    response = client.post("/api/processes/restart-test/restart")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "started"

    # Clean up
    client.post("/api/processes/restart-test/stop")


# Logs endpoint tests


def test_get_logs_empty(client):
    """Test getting logs for a process with no logs."""
    # Create a process
    client.post(
        "/api/processes",
        json={
            "name": "logs-test",
            "command": "echo hello",
        },
    )

    response = client.get("/api/logs/logs-test")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["logs"] == []


def test_get_logs_with_tail(client):
    """Test getting logs with tail parameter."""
    # Create a process
    client.post(
        "/api/processes",
        json={
            "name": "logs-tail-test",
            "command": "echo hello",
        },
    )

    response = client.get("/api/logs/logs-tail-test?tail=50")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_get_logs_not_found(client):
    """Test getting logs for nonexistent process."""
    response = client.get("/api/logs/nonexistent")
    assert response.status_code == 404


# Snippets endpoint tests


def test_list_snippets_empty(client):
    """Test listing snippets when none exist."""
    response = client.get("/api/snippets")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["snippets"] == []


def test_create_snippet(client):
    """Test creating a snippet via API."""
    response = client.post(
        "/api/snippets",
        json={
            "name": "test-snippet",
            "command": "echo hello",
            "description": "Test snippet",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["action"] == "created"
    assert data["data"]["snippet"]["name"] == "test-snippet"


def test_create_snippet_with_tags(client):
    """Test creating a snippet with tags."""
    response = client.post(
        "/api/snippets",
        json={
            "name": "tagged-snippet",
            "command": "docker build .",
            "tags": ["docker", "build"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["snippet"]["tags"] == ["docker", "build"]


def test_list_snippets_with_tag_filter(client):
    """Test filtering snippets by tag."""
    # Create snippets with different tags
    client.post(
        "/api/snippets",
        json={
            "name": "docker-snippet",
            "command": "docker ps",
            "tags": ["docker"],
        },
    )
    client.post(
        "/api/snippets",
        json={
            "name": "npm-snippet",
            "command": "npm install",
            "tags": ["npm"],
        },
    )

    # Filter by docker tag
    response = client.get("/api/snippets?tag=docker")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["count"] == 1
    assert data["data"]["snippets"][0]["name"] == "docker-snippet"


def test_get_snippet(client):
    """Test getting a specific snippet."""
    # Create a snippet
    client.post(
        "/api/snippets",
        json={
            "name": "get-snippet-test",
            "command": "echo test",
        },
    )

    response = client.get("/api/snippets/get-snippet-test")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["snippet"]["name"] == "get-snippet-test"


def test_get_snippet_not_found(client):
    """Test getting a snippet that doesn't exist."""
    response = client.get("/api/snippets/nonexistent")
    assert response.status_code == 404


def test_delete_snippet(client):
    """Test deleting a snippet."""
    # Create a snippet
    client.post(
        "/api/snippets",
        json={
            "name": "delete-snippet-test",
            "command": "echo test",
        },
    )

    response = client.delete("/api/snippets/delete-snippet-test")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["action"] == "removed"


def test_delete_snippet_not_found(client):
    """Test deleting a snippet that doesn't exist."""
    response = client.delete("/api/snippets/nonexistent")
    assert response.status_code == 404


def test_run_snippet(client):
    """Test running a snippet via API."""
    # Create a snippet
    client.post(
        "/api/snippets",
        json={
            "name": "run-snippet-test",
            "command": "echo hello from api",
        },
    )

    response = client.post("/api/snippets/run-snippet-test/run")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["snippet"] == "run-snippet-test"
    assert "hello from api" in data["data"]["stdout"]
    assert data["data"]["exit_code"] == 0


def test_run_snippet_not_found(client):
    """Test running a snippet that doesn't exist."""
    response = client.post("/api/snippets/nonexistent/run")
    assert response.status_code == 404
