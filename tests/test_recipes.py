"""Tests for recipe execution functionality."""

import pytest

from procler.config import loader as config_loader
from procler.core.recipes import get_recipe_executor, reset_recipe_executor


@pytest.fixture
def recipe_config(tmp_path):
    """Create a temporary config with recipes defined."""
    config_dir = tmp_path / ".procler"
    config_dir.mkdir()
    config_file = config_dir / "config.yaml"
    config_file.write_text("""
version: 1

processes:
  api:
    command: "echo api started && sleep 5"
    description: "API server"
  worker:
    command: "echo worker started && sleep 5"
    description: "Background worker"

groups:
  backend:
    processes: [api, worker]

recipes:
  deploy:
    description: "Graceful deployment"
    on_error: stop
    steps:
      - stop: worker
      - stop: api
      - wait: 100ms
      - exec: "echo 'Running migrations'"
      - start: api
      - start: worker

  restart_all:
    description: "Restart everything"
    on_error: continue
    steps:
      - group_stop: backend
      - wait: 100ms
      - group_start: backend

  simple:
    description: "Simple exec recipe"
    steps:
      - exec: "echo hello"
      - wait: 50ms
      - exec: "echo world"
""")

    # Point config loader to this directory
    import os

    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    config_loader.reset_config_cache()

    yield config_dir

    os.chdir(old_cwd)
    config_loader.reset_config_cache()


def test_recipe_executor_singleton():
    """Test that RecipeExecutor is a singleton."""
    executor1 = get_recipe_executor()
    executor2 = get_recipe_executor()
    assert executor1 is executor2

    reset_recipe_executor()
    executor3 = get_recipe_executor()
    assert executor1 is not executor3


def test_list_recipes_empty():
    """Test listing recipes when none are defined."""
    executor = get_recipe_executor()
    result = executor.list_recipes()

    assert result["success"] is True
    assert result["data"]["count"] == 0
    assert result["data"]["recipes"] == []


def test_list_recipes(recipe_config):
    """Test listing recipes."""
    executor = get_recipe_executor()
    result = executor.list_recipes()

    assert result["success"] is True
    assert result["data"]["count"] == 3

    recipe_names = [r["name"] for r in result["data"]["recipes"]]
    assert "deploy" in recipe_names
    assert "restart_all" in recipe_names
    assert "simple" in recipe_names


def test_get_recipe(recipe_config):
    """Test getting a specific recipe."""
    executor = get_recipe_executor()
    result = executor.get_recipe("deploy")

    assert result["success"] is True
    assert result["data"]["recipe"]["name"] == "deploy"
    assert result["data"]["recipe"]["description"] == "Graceful deployment"
    assert result["data"]["recipe"]["on_error"] == "stop"
    assert len(result["data"]["recipe"]["steps"]) == 6


def test_get_recipe_not_found(recipe_config):
    """Test getting a non-existent recipe."""
    executor = get_recipe_executor()
    result = executor.get_recipe("nonexistent")

    assert result["success"] is False
    assert result["error_code"] == "recipe_not_found"


@pytest.mark.asyncio
async def test_dry_run_recipe(recipe_config):
    """Test dry running a recipe."""
    executor = get_recipe_executor()
    result = await executor.run_recipe("simple", dry_run=True)

    assert result["success"] is True
    assert result["data"]["dry_run"] is True
    assert result["data"]["recipe"] == "simple"
    assert len(result["data"]["planned_steps"]) == 3

    # Steps should be previewed, not executed
    for step in result["data"]["planned_steps"]:
        assert "step" in step
        assert "action" in step


@pytest.mark.asyncio
async def test_run_simple_recipe(recipe_config):
    """Test running a simple recipe with exec steps."""
    executor = get_recipe_executor()
    result = await executor.run_recipe("simple")

    assert result["success"] is True
    assert result["data"]["recipe"] == "simple"
    assert len(result["data"]["results"]) == 3

    # All steps should succeed
    for step_result in result["data"]["results"]:
        assert step_result["success"] is True


@pytest.mark.asyncio
async def test_run_recipe_not_found(recipe_config):
    """Test running a non-existent recipe."""
    executor = get_recipe_executor()
    result = await executor.run_recipe("nonexistent")

    assert result["success"] is False
    assert result["error_code"] == "recipe_not_found"


@pytest.mark.asyncio
async def test_run_recipe_with_processes(recipe_config):
    """Test running a recipe that manages processes."""
    executor = get_recipe_executor()

    # Run the deploy recipe with continue_on_error so we see all steps
    result = await executor.run_recipe("deploy", continue_on_error=True)

    # The recipe runs with 6 steps
    assert result["data"]["recipe"] == "deploy"
    assert result["data"]["steps_total"] == 6
    assert result["data"]["steps_completed"] == 6

    # Check action descriptions contain expected keywords
    actions = [r.get("action", "") for r in result["data"]["results"]]
    assert any("stop" in a for a in actions)
    assert any("exec" in a for a in actions)
    assert any("start" in a for a in actions)
    assert any("wait" in a for a in actions)


@pytest.mark.asyncio
async def test_run_recipe_with_group(recipe_config):
    """Test running a recipe with group operations."""
    executor = get_recipe_executor()

    result = await executor.run_recipe("restart_all")

    # Check recipe was processed
    assert result["data"]["recipe"] == "restart_all"
    assert result["data"]["steps_total"] == 3

    # Check group operations were executed (via action descriptions)
    actions = [r.get("action", "") for r in result["data"]["results"]]
    assert any("group" in a for a in actions)


@pytest.mark.asyncio
async def test_run_recipe_continue_on_error(recipe_config):
    """Test recipe with continue_on_error option."""
    executor = get_recipe_executor()

    # restart_all has on_error: continue
    result = await executor.run_recipe("restart_all", continue_on_error=True)

    # Should complete even if some steps fail
    assert result["data"]["recipe"] == "restart_all"


def test_recipe_steps_preview(recipe_config):
    """Test that recipe steps are correctly parsed."""
    executor = get_recipe_executor()
    result = executor.get_recipe("deploy")

    steps = result["data"]["recipe"]["steps"]

    # Steps are raw dicts from YAML
    assert "stop" in steps[0]  # {stop: worker}
    assert "stop" in steps[1]  # {stop: api}
    assert "wait" in steps[2]  # {wait: 100ms}
    assert "exec" in steps[3]  # {exec: ...}
    assert "start" in steps[4]  # {start: api}
    assert "start" in steps[5]  # {start: worker}
