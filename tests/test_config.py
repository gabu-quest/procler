"""Tests for configuration loading and validation."""

import pytest
from pathlib import Path

from procler.config import (
    load_config,
    get_config,
    reload_config,
    generate_template_config,
    find_config_dir,
    get_config_file_path,
    ProclerConfig,
    ProcessDef,
    GroupDef,
    RecipeDef,
    SnippetDef,
    HealthCheckDef,
    DependencyCondition,
    DependencyDef,
    ContextType,
)
from procler.config import loader as config_loader
from procler.config.schema import parse_recipe_step


@pytest.fixture
def config_dir(tmp_path):
    """Create a temporary config directory."""
    config_dir = tmp_path / ".procler"
    config_dir.mkdir()

    # Change working directory
    import os
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    config_loader.reset_config_cache()

    yield config_dir

    os.chdir(old_cwd)
    config_loader.reset_config_cache()


@pytest.fixture
def sample_config(config_dir):
    """Create a sample config file."""
    config_file = config_dir / "config.yaml"
    config_file.write_text("""
version: 1

processes:
  api:
    command: uvicorn main:app --reload
    context: local
    cwd: /app
    tags: [backend, api]
    description: "API server"
  db:
    command: docker run postgres
    context: docker
    container: my-postgres
    tags: [database]
  worker:
    command: celery worker
    depends_on:
      - db
      - name: api
        condition: healthy
    healthcheck:
      test: curl -f http://localhost:8080/health
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 30s

groups:
  backend:
    description: "Full backend"
    processes: [db, api, worker]

recipes:
  deploy:
    description: "Deploy app"
    on_error: stop
    steps:
      - stop: worker
      - wait: 2s
      - start: worker

snippets:
  rebuild:
    command: docker compose build
    description: "Rebuild all containers"
    tags: [docker]
""")
    config_loader.reset_config_cache()
    return config_file


def test_find_config_dir(config_dir):
    """Test config directory discovery."""
    found = find_config_dir()
    assert found is not None
    assert found.name == ".procler"


def test_load_config(sample_config):
    """Test loading config from file."""
    config = load_config()

    assert config.version == 1
    assert len(config.processes) == 3
    assert len(config.groups) == 1
    assert len(config.recipes) == 1
    assert len(config.snippets) == 1


def test_get_config_caching(sample_config):
    """Test that get_config returns cached config."""
    config1 = get_config()
    config2 = get_config()
    assert config1 is config2


def test_reload_config(sample_config):
    """Test that reload_config returns fresh config."""
    config1 = get_config()
    config2 = reload_config()

    # Should be same content but different objects after reload
    assert config1.version == config2.version


def test_generate_template_config(config_dir):
    """Test template config generation."""
    # generate_template_config returns a string template
    content = generate_template_config()

    # Template should have all sections
    assert "version: 1" in content
    assert "processes:" in content
    assert "groups:" in content
    assert "recipes:" in content
    assert "snippets:" in content

    # Template has helpful comments
    assert "LLM-First" in content
    assert "VERSION CONTROLLED" in content

    # Should have example entries (commented out)
    assert "# api:" in content or "#   api:" in content
    assert "Example" in content


# Schema tests

def test_process_def():
    """Test ProcessDef model."""
    proc = ProcessDef(
        command="echo hello",
        context=ContextType.LOCAL,
        tags=["test"],
        description="Test process",
    )

    assert proc.command == "echo hello"
    assert proc.context == ContextType.LOCAL
    assert proc.tags == ["test"]
    assert proc.container is None


def test_process_def_docker():
    """Test ProcessDef with docker context."""
    proc = ProcessDef(
        command="python app.py",
        context=ContextType.DOCKER,
        container="my-container",
    )

    assert proc.context == ContextType.DOCKER
    assert proc.container == "my-container"


def test_process_def_dependencies(sample_config):
    """Test ProcessDef with dependencies."""
    config = get_config()
    worker = config.processes["worker"]

    deps = worker.get_dependencies()
    assert len(deps) == 2

    # First is simple string dependency
    assert deps[0].name == "db"
    assert deps[0].condition == DependencyCondition.STARTED

    # Second has explicit condition
    assert deps[1].name == "api"
    assert deps[1].condition == DependencyCondition.HEALTHY


def test_process_def_healthcheck(sample_config):
    """Test ProcessDef with healthcheck."""
    config = get_config()
    worker = config.processes["worker"]

    hc = worker.healthcheck
    assert hc is not None
    assert hc.test == "curl -f http://localhost:8080/health"
    assert hc.get_interval_seconds() == 10.0
    assert hc.get_timeout_seconds() == 5.0
    assert hc.retries == 3
    assert hc.get_start_period_seconds() == 30.0


def test_health_check_def():
    """Test HealthCheckDef model."""
    hc = HealthCheckDef(
        test="curl -f http://localhost/health",
        interval="5s",
        timeout="2s",
        retries=5,
        start_period="1m",
    )

    assert hc.get_interval_seconds() == 5.0
    assert hc.get_timeout_seconds() == 2.0
    assert hc.get_start_period_seconds() == 60.0
    assert hc.retries == 5


def test_health_check_duration_parsing():
    """Test parsing different duration formats."""
    hc = HealthCheckDef(test="test")

    # Default values
    assert hc.get_interval_seconds() == 10.0
    assert hc.get_timeout_seconds() == 5.0

    # Test milliseconds
    hc.interval = "500ms"
    assert hc.get_interval_seconds() == 0.5

    # Test minutes
    hc.interval = "2m"
    assert hc.get_interval_seconds() == 120.0


def test_group_def():
    """Test GroupDef model."""
    group = GroupDef(
        processes=["a", "b", "c"],
        description="Test group",
    )

    assert group.processes == ["a", "b", "c"]
    # Default stop order is reversed
    assert group.get_stop_order() == ["c", "b", "a"]


def test_group_def_custom_stop_order():
    """Test GroupDef with custom stop order."""
    group = GroupDef(
        processes=["a", "b", "c"],
        stop_order=["a", "c", "b"],
    )

    assert group.get_stop_order() == ["a", "c", "b"]


def test_recipe_step_parsing():
    """Test recipe step parsing."""
    # Start step
    step = parse_recipe_step({"start": "api"})
    assert step.start == "api"

    # Stop step
    step = parse_recipe_step({"stop": "api", "ignore_error": True})
    assert step.stop == "api"
    assert step.ignore_error is True

    # Wait step
    step = parse_recipe_step({"wait": "5s"})
    assert step.wait == "5s"
    assert step.get_seconds() == 5.0

    # Exec step
    step = parse_recipe_step({"exec": "echo hello", "timeout": "30s"})
    assert step.exec == "echo hello"
    assert step.get_timeout_seconds() == 30.0


def test_recipe_step_wait_durations():
    """Test wait step duration parsing."""
    from procler.config.schema import RecipeStepWait

    # Seconds
    step = RecipeStepWait(wait="10s")
    assert step.get_seconds() == 10.0

    # Milliseconds
    step = RecipeStepWait(wait="100ms")
    assert step.get_seconds() == 0.1

    # Minutes
    step = RecipeStepWait(wait="2m")
    assert step.get_seconds() == 120.0

    # No unit (assumes seconds)
    step = RecipeStepWait(wait="5")
    assert step.get_seconds() == 5.0


def test_snippet_def():
    """Test SnippetDef model."""
    snippet = SnippetDef(
        command="npm run build",
        description="Build the project",
        tags=["build", "npm"],
    )

    assert snippet.command == "npm run build"
    assert snippet.description == "Build the project"
    assert snippet.tags == ["build", "npm"]
    assert snippet.context == ContextType.LOCAL


def test_config_validate_references(config_dir):
    """Test config reference validation."""
    config_file = config_dir / "config.yaml"
    config_file.write_text("""
version: 1

processes:
  api:
    command: echo api

groups:
  bad_group:
    processes: [api, nonexistent]

recipes:
  bad_recipe:
    steps:
      - start: ghost_process
""")
    config_loader.reset_config_cache()

    config = get_config()
    errors = config.validate_references()

    assert len(errors) >= 2
    assert any("nonexistent" in e for e in errors)
    assert any("ghost_process" in e for e in errors)


def test_config_docker_without_container(config_dir):
    """Test validation catches docker context without container."""
    config_file = config_dir / "config.yaml"
    config_file.write_text("""
version: 1

processes:
  bad_docker:
    command: python app.py
    context: docker
    # Missing container!
""")
    config_loader.reset_config_cache()

    config = get_config()
    errors = config.validate_references()

    assert any("docker context but no container" in e for e in errors)


def test_empty_config(config_dir):
    """Test loading minimal config."""
    config_file = config_dir / "config.yaml"
    config_file.write_text("""
version: 1
""")
    config_loader.reset_config_cache()

    config = get_config()

    assert config.version == 1
    assert len(config.processes) == 0
    assert len(config.groups) == 0
    assert len(config.recipes) == 0
    assert len(config.snippets) == 0


def test_dependency_def():
    """Test DependencyDef model."""
    # Simple
    dep = DependencyDef(name="api")
    assert dep.name == "api"
    assert dep.condition == DependencyCondition.STARTED

    # With healthy condition
    dep = DependencyDef(name="db", condition=DependencyCondition.HEALTHY)
    assert dep.condition == DependencyCondition.HEALTHY
