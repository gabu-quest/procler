"""Tests for process groups functionality."""

import pytest

from procler.core.groups import GroupManager, get_group_manager, reset_group_manager
from procler.config import loader as config_loader


@pytest.fixture
def group_config(tmp_path):
    """Create a temporary config with groups defined."""
    config_dir = tmp_path / ".procler"
    config_dir.mkdir()
    config_file = config_dir / "config.yaml"
    config_file.write_text("""
version: 1

processes:
  redis:
    command: "echo redis started && sleep 10"
    description: "Redis server"
  api:
    command: "echo api started && sleep 10"
    description: "API server"
  worker:
    command: "echo worker started && sleep 10"
    description: "Background worker"

groups:
  backend:
    description: "Full backend stack"
    processes:
      - redis
      - api
      - worker
  minimal:
    description: "Minimal stack"
    processes:
      - api
    stop_order:
      - api
""")

    # Point config loader to this directory
    import os
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    config_loader.reset_config_cache()

    yield config_dir

    os.chdir(old_cwd)
    config_loader.reset_config_cache()


def test_group_manager_singleton():
    """Test that GroupManager is a singleton."""
    manager1 = get_group_manager()
    manager2 = get_group_manager()
    assert manager1 is manager2

    reset_group_manager()
    manager3 = get_group_manager()
    assert manager1 is not manager3


def test_list_groups_empty():
    """Test listing groups when none are defined."""
    manager = get_group_manager()
    result = manager.list_groups()

    assert result["success"] is True
    assert result["data"]["count"] == 0
    assert result["data"]["groups"] == []


def test_list_groups(group_config):
    """Test listing groups."""
    manager = get_group_manager()
    result = manager.list_groups()

    assert result["success"] is True
    assert result["data"]["count"] == 2

    group_names = [g["name"] for g in result["data"]["groups"]]
    assert "backend" in group_names
    assert "minimal" in group_names


def test_get_group(group_config):
    """Test getting a specific group."""
    manager = get_group_manager()
    result = manager.get_group("backend")

    assert result["success"] is True
    assert result["data"]["group"]["name"] == "backend"
    assert result["data"]["group"]["description"] == "Full backend stack"
    assert result["data"]["group"]["processes"] == ["redis", "api", "worker"]
    # Stop order should be reversed by default
    assert result["data"]["group"]["stop_order"] == ["worker", "api", "redis"]


def test_get_group_not_found(group_config):
    """Test getting a non-existent group."""
    manager = get_group_manager()
    result = manager.get_group("nonexistent")

    assert result["success"] is False
    assert result["error_code"] == "group_not_found"
    assert "nonexistent" in result["error"]


def test_get_group_custom_stop_order(group_config):
    """Test group with custom stop order."""
    manager = get_group_manager()
    result = manager.get_group("minimal")

    assert result["success"] is True
    assert result["data"]["group"]["stop_order"] == ["api"]


@pytest.mark.asyncio
async def test_start_group(group_config):
    """Test starting a group of processes."""
    manager = get_group_manager()
    result = await manager.start_group("backend")

    assert result["success"] is True
    assert result["data"]["group"] == "backend"
    assert result["data"]["action"] == "started"
    assert len(result["data"]["results"]) == 3

    # All processes should have started successfully
    for proc_result in result["data"]["results"]:
        assert proc_result["success"] is True


@pytest.mark.asyncio
async def test_start_group_not_found(group_config):
    """Test starting a non-existent group."""
    manager = get_group_manager()
    result = await manager.start_group("nonexistent")

    assert result["success"] is False
    assert result["error_code"] == "group_not_found"


@pytest.mark.asyncio
async def test_stop_group(group_config):
    """Test stopping a group of processes."""
    manager = get_group_manager()

    # First start the group
    await manager.start_group("backend")

    # Then stop it
    result = await manager.stop_group("backend")

    assert result["success"] is True
    assert result["data"]["group"] == "backend"
    assert result["data"]["action"] == "stopped"
    assert len(result["data"]["results"]) == 3


@pytest.mark.asyncio
async def test_stop_group_not_found(group_config):
    """Test stopping a non-existent group."""
    manager = get_group_manager()
    result = await manager.stop_group("nonexistent")

    assert result["success"] is False
    assert result["error_code"] == "group_not_found"


@pytest.mark.asyncio
async def test_status_group(group_config):
    """Test getting status of a group."""
    manager = get_group_manager()

    # Start the group first
    await manager.start_group("backend")

    # Get status
    result = await manager.status_group("backend")

    assert result["success"] is True
    assert result["data"]["group"] == "backend"
    assert result["data"]["description"] == "Full backend stack"
    assert len(result["data"]["statuses"]) == 3

    # All should be running
    for status in result["data"]["statuses"]:
        assert status["status"] == "running"


@pytest.mark.asyncio
async def test_status_group_not_found(group_config):
    """Test getting status of a non-existent group."""
    manager = get_group_manager()
    result = await manager.status_group("nonexistent")

    assert result["success"] is False
    assert result["error_code"] == "group_not_found"
