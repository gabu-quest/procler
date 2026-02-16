"""Contract tests: prove README examples and documented behaviors work.

Each test corresponds to a [C##] contract marker in README.md.
If a README claim changes, the corresponding test here must be updated too.
"""

import json
import os
from pathlib import Path

import pytest
from click.testing import CliRunner

from procler.cli import cli
from procler.config import loader as config_loader


@pytest.fixture
def runner():
    """CLI test runner."""
    return CliRunner()


@pytest.fixture
def config_dir(tmp_path):
    """Create a temporary config directory and chdir to it."""
    config_path = tmp_path / ".procler"
    config_path.mkdir()
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    config_loader.reset_config_cache()
    yield config_path
    os.chdir(old_cwd)
    config_loader.reset_config_cache()


@pytest.fixture
def sample_config(config_dir):
    """Write a config file with processes, groups, recipes, and snippets."""
    config_file = config_dir / "config.yaml"
    config_file.write_text("""\
version: 1

vars:
  API_PORT: "8000"
  DB_CONTAINER: postgres-dev

processes:
  redis:
    command: echo redis-server
  db:
    command: echo postgres
    healthcheck:
      tcp_socket: "localhost:5432"
      interval: 5s
      timeout: 3s
  api:
    command: echo uvicorn main:app --port ${API_PORT}
    namespace: backend
    tags: [backend, api]
    ready_log_line: "Uvicorn running on"
  worker:
    command: echo celery worker
    namespace: backend
    depends_on:
      - redis
      - name: api
        condition: log_ready

groups:
  backend:
    description: "Full backend stack"
    processes: [redis, db, api, worker]
    stop_order: [worker, api, db, redis]

recipes:
  deploy:
    description: "Graceful deployment"
    on_error: stop
    steps:
      - stop: worker
      - stop: api
      - wait: 1s
      - start: api
      - start: worker

snippets:
  rebuild:
    command: docker compose build
    description: "Rebuild containers"
    tags: [docker]
""")
    config_loader.reset_config_cache()
    return config_file


# ---------------------------------------------------------------------------
# [C01] Basic workflow: define → start → status → logs → stop
# ---------------------------------------------------------------------------


class TestC01BasicLifecycle:
    """[C01] Basic process lifecycle as documented in README Quick Start."""

    def test_define_creates_process(self, runner):
        result = runner.invoke(cli, ["define", "--name", "my-api", "--command", "sleep 30"])
        data = json.loads(result.output)
        assert data["success"] is True
        assert data["data"]["action"] == "created"
        assert data["data"]["process"]["name"] == "my-api"

    def test_start_returns_running(self, runner):
        runner.invoke(cli, ["define", "--name", "my-api", "--command", "sleep 30"])
        result = runner.invoke(cli, ["start", "my-api"])
        data = json.loads(result.output)
        assert data["success"] is True
        assert data["data"]["status"] == "started"
        assert data["data"]["process"]["status"] == "running"
        assert isinstance(data["data"]["process"]["pid"], int)
        runner.invoke(cli, ["stop", "my-api"])

    def test_status_shows_running_process(self, runner):
        runner.invoke(cli, ["define", "--name", "my-api", "--command", "sleep 30"])
        runner.invoke(cli, ["start", "my-api"])
        result = runner.invoke(cli, ["status", "my-api"])
        data = json.loads(result.output)
        assert data["success"] is True
        proc = data["data"]["process"]
        assert proc["status"] == "running"
        assert proc["pid"] is not None
        runner.invoke(cli, ["stop", "my-api"])

    def test_logs_returns_log_entries(self, runner):
        runner.invoke(cli, ["define", "--name", "my-api", "--command", "echo hello-from-api"])
        runner.invoke(cli, ["start", "my-api"])
        # Give the process a moment to produce output
        import time

        time.sleep(0.5)
        result = runner.invoke(cli, ["logs", "my-api", "--tail", "10"])
        data = json.loads(result.output)
        assert data["success"] is True
        assert "logs" in data["data"]
        runner.invoke(cli, ["stop", "my-api"])

    def test_stop_returns_stopped(self, runner):
        runner.invoke(cli, ["define", "--name", "my-api", "--command", "sleep 30"])
        runner.invoke(cli, ["start", "my-api"])
        result = runner.invoke(cli, ["stop", "my-api"])
        data = json.loads(result.output)
        assert data["success"] is True
        assert data["data"]["status"] == "stopped"

    def test_full_lifecycle(self, runner):
        """Complete define → start → status → stop cycle."""
        # Define
        r = runner.invoke(cli, ["define", "--name", "test-api", "--command", "sleep 30"])
        assert json.loads(r.output)["success"] is True

        # Start
        r = runner.invoke(cli, ["start", "test-api"])
        start_data = json.loads(r.output)
        assert start_data["success"] is True
        pid = start_data["data"]["process"]["pid"]
        assert isinstance(pid, int)

        # Status
        r = runner.invoke(cli, ["status", "test-api"])
        status_data = json.loads(r.output)
        assert status_data["data"]["process"]["status"] == "running"
        assert status_data["data"]["process"]["pid"] == pid

        # Stop
        r = runner.invoke(cli, ["stop", "test-api"])
        assert json.loads(r.output)["data"]["status"] == "stopped"


# ---------------------------------------------------------------------------
# [C02] JSON response structure: {success, data?, error?, error_code?, suggestion?}
# ---------------------------------------------------------------------------


class TestC02JsonResponseStructure:
    """[C02] All CLI responses follow the documented JSON envelope."""

    def test_success_response_has_success_and_data(self, runner):
        result = runner.invoke(cli, ["capabilities"])
        data = json.loads(result.output)
        assert "success" in data
        assert data["success"] is True
        assert "data" in data

    def test_status_response_has_success_and_data(self, runner):
        result = runner.invoke(cli, ["status"])
        data = json.loads(result.output)
        assert isinstance(data["success"], bool)
        assert "data" in data

    def test_list_response_has_success_and_data(self, runner):
        result = runner.invoke(cli, ["list"])
        data = json.loads(result.output)
        assert data["success"] is True
        assert "data" in data


# ---------------------------------------------------------------------------
# [C03] Error response structure: error_code + suggestion on all errors
# ---------------------------------------------------------------------------


class TestC03ErrorResponseContract:
    """[C03] Every error response includes error_code and suggestion."""

    def test_start_nonexistent_has_error_code_and_suggestion(self, runner):
        result = runner.invoke(cli, ["start", "ghost"])
        data = json.loads(result.output)
        assert data["success"] is False
        assert "error" in data
        assert "error_code" in data
        assert data["error_code"] == "process_not_found"
        assert "suggestion" in data

    def test_stop_nonexistent_has_error_code_and_suggestion(self, runner):
        result = runner.invoke(cli, ["stop", "ghost"])
        data = json.loads(result.output)
        assert data["success"] is False
        assert data["error_code"] == "process_not_found"
        assert "suggestion" in data

    def test_define_docker_without_container(self, runner):
        result = runner.invoke(
            cli, ["define", "--name", "x", "--command", "echo", "--context", "docker"]
        )
        data = json.loads(result.output)
        assert data["success"] is False
        assert data["error_code"] == "missing_container"
        assert "suggestion" in data

    def test_define_duplicate_without_force(self, runner):
        runner.invoke(cli, ["define", "--name", "dup", "--command", "echo"])
        result = runner.invoke(cli, ["define", "--name", "dup", "--command", "echo"])
        data = json.loads(result.output)
        assert data["success"] is False
        assert data["error_code"] == "process_exists"
        assert "suggestion" in data

    def test_remove_nonexistent(self, runner):
        result = runner.invoke(cli, ["remove", "ghost"])
        data = json.loads(result.output)
        assert data["success"] is False
        assert data["error_code"] == "process_not_found"
        assert "suggestion" in data


# ---------------------------------------------------------------------------
# [C04] Group start respects dependency order
# ---------------------------------------------------------------------------


class TestC04GroupOrchestration:
    """[C04] Groups define ordered start and custom stop order."""

    def test_group_defines_process_order(self, sample_config):
        from procler.config import get_config

        cfg = get_config()
        group = cfg.groups["backend"]
        assert group.processes == ["redis", "db", "api", "worker"]

    def test_group_custom_stop_order(self, sample_config):
        from procler.config import get_config

        cfg = get_config()
        group = cfg.groups["backend"]
        assert group.get_stop_order() == ["worker", "api", "db", "redis"]

    def test_group_default_stop_order_is_reversed(self):
        from procler.config.schema import GroupDef

        group = GroupDef(processes=["a", "b", "c"])
        assert group.get_stop_order() == ["c", "b", "a"]


# ---------------------------------------------------------------------------
# [C05] Recipe dry-run previews without executing
# ---------------------------------------------------------------------------


class TestC05RecipeDryRun:
    """[C05] Recipe dry-run shows steps without executing them."""

    def test_recipe_dry_run_returns_steps(self, runner, sample_config):
        result = runner.invoke(cli, ["recipe", "run", "deploy", "--dry-run"])
        data = json.loads(result.output)
        assert data["success"] is True
        assert data["data"]["dry_run"] is True
        assert "planned_steps" in data["data"]
        assert len(data["data"]["planned_steps"]) == 5  # stop, stop, wait, start, start

    def test_recipe_list_shows_recipes(self, runner, sample_config):
        result = runner.invoke(cli, ["recipe", "list"])
        data = json.loads(result.output)
        assert data["success"] is True
        recipes = data["data"]["recipes"]
        assert len(recipes) == 1
        assert recipes[0]["name"] == "deploy"


# ---------------------------------------------------------------------------
# [C06] Snippet save → list → run → remove lifecycle
# ---------------------------------------------------------------------------


class TestC06SnippetLifecycle:
    """[C06] Full snippet CRUD lifecycle."""

    def test_snippet_save(self, runner):
        result = runner.invoke(
            cli,
            ["snippet", "save", "--name", "rebuild", "--command", "echo build", "--tags", "docker"],
        )
        data = json.loads(result.output)
        assert data["success"] is True

    def test_snippet_list(self, runner):
        runner.invoke(
            cli,
            ["snippet", "save", "--name", "rebuild", "--command", "echo build", "--tags", "docker"],
        )
        result = runner.invoke(cli, ["snippet", "list"])
        data = json.loads(result.output)
        assert data["success"] is True
        assert len(data["data"]["snippets"]) == 1
        assert data["data"]["snippets"][0]["name"] == "rebuild"

    def test_snippet_list_filter_by_tag(self, runner):
        runner.invoke(
            cli,
            ["snippet", "save", "--name", "s1", "--command", "echo a", "--tags", "docker"],
        )
        runner.invoke(
            cli,
            ["snippet", "save", "--name", "s2", "--command", "echo b", "--tags", "npm"],
        )
        result = runner.invoke(cli, ["snippet", "list", "--tag", "docker"])
        data = json.loads(result.output)
        assert data["success"] is True
        assert len(data["data"]["snippets"]) == 1
        assert data["data"]["snippets"][0]["name"] == "s1"

    def test_snippet_run(self, runner):
        runner.invoke(
            cli,
            ["snippet", "save", "--name", "greet", "--command", "echo hello"],
        )
        result = runner.invoke(cli, ["snippet", "run", "greet"])
        data = json.loads(result.output)
        assert data["success"] is True

    def test_snippet_remove(self, runner):
        runner.invoke(
            cli,
            ["snippet", "save", "--name", "rm-me", "--command", "echo bye"],
        )
        result = runner.invoke(cli, ["snippet", "remove", "rm-me"])
        data = json.loads(result.output)
        assert data["success"] is True

        # Verify it's gone
        result = runner.invoke(cli, ["snippet", "list"])
        snippets = json.loads(result.output)["data"]["snippets"]
        assert len(snippets) == 0


# ---------------------------------------------------------------------------
# [C07] Config init creates .procler/ directory
# ---------------------------------------------------------------------------


class TestC07ConfigInit:
    """[C07] procler config init creates the .procler/ directory."""

    def test_config_init_creates_directory(self, runner, tmp_path):
        target_dir = tmp_path / "init-test" / ".procler"
        old_cwd = os.getcwd()
        old_env = os.environ.get("PROCLER_CONFIG_DIR")
        os.environ["PROCLER_CONFIG_DIR"] = str(target_dir)
        config_loader.reset_config_cache()
        try:
            result = runner.invoke(cli, ["config", "init"])
            data = json.loads(result.output)
            assert data["success"] is True
            assert data["data"]["action"] == "initialized"
            assert "config.yaml" in data["data"]["files_created"]
            assert ".gitignore" in data["data"]["files_created"]

            # Verify files exist
            assert target_dir.exists()
            assert (target_dir / "config.yaml").exists()
            assert (target_dir / ".gitignore").exists()
        finally:
            os.chdir(old_cwd)
            if old_env is None:
                os.environ.pop("PROCLER_CONFIG_DIR", None)
            else:
                os.environ["PROCLER_CONFIG_DIR"] = old_env
            config_loader.reset_config_cache()

    def test_config_init_refuses_without_force(self, runner, config_dir):
        (config_dir / "config.yaml").write_text("version: 1\n")
        result = runner.invoke(cli, ["config", "init"])
        data = json.loads(result.output)
        assert data["success"] is False
        assert data["error_code"] == "config_exists"


# ---------------------------------------------------------------------------
# [C08] Config validate catches invalid references
# ---------------------------------------------------------------------------


class TestC08ConfigValidate:
    """[C08] procler config validate catches invalid references."""

    def test_validate_valid_config(self, runner, sample_config):
        result = runner.invoke(cli, ["config", "validate"])
        data = json.loads(result.output)
        assert data["success"] is True
        assert data["data"]["valid"] is True

    def test_validate_catches_bad_references(self, runner, config_dir):
        (config_dir / "config.yaml").write_text("""\
version: 1
processes:
  api:
    command: echo api
groups:
  broken:
    processes: [api, ghost_process]
""")
        config_loader.reset_config_cache()
        result = runner.invoke(cli, ["config", "validate"])
        data = json.loads(result.output)
        assert data["success"] is False
        assert data["error_code"] == "validation_failed"
        assert any("ghost_process" in e for e in data["errors"])


# ---------------------------------------------------------------------------
# [C09] Variable substitution in commands
# ---------------------------------------------------------------------------


class TestC09VariableSubstitution:
    """[C09] ${VAR} in commands gets substituted from config.vars."""

    def test_substitute_vars_replaces_variables(self):
        from procler.core.variable_substitution import substitute_vars

        result = substitute_vars("uvicorn --port ${PORT}", {"PORT": "8000"})
        assert result == "uvicorn --port 8000"

    def test_substitute_vars_keeps_unknown(self):
        from procler.core.variable_substitution import substitute_vars

        result = substitute_vars("echo ${UNKNOWN}", {"PORT": "8000"})
        assert result == "echo ${UNKNOWN}"

    def test_substitute_vars_multiple(self):
        from procler.core.variable_substitution import substitute_vars

        result = substitute_vars("${HOST}:${PORT}", {"HOST": "0.0.0.0", "PORT": "9000"})
        assert result == "0.0.0.0:9000"

    def test_list_resolve_substitutes(self, runner, sample_config):
        """CLI list --resolve applies variable substitution."""
        # First define a process with a variable in the command
        runner.invoke(
            cli,
            ["define", "--name", "api-test", "--command", "echo ${API_PORT}"],
        )
        result = runner.invoke(cli, ["list", "--resolve"])
        data = json.loads(result.output)
        assert data["success"] is True
        # The process defined in runtime DB should have variables resolved
        procs = data["data"]["processes"]
        api_proc = next((p for p in procs if p["name"] == "api-test"), None)
        assert api_proc is not None
        assert api_proc["command"] == "echo 8000"


# ---------------------------------------------------------------------------
# [C10] Export systemd generates valid .service file
# ---------------------------------------------------------------------------


class TestC10ExportSystemd:
    """[C10] Export produces valid systemd unit files."""

    def test_export_systemd_has_required_sections(self, runner, sample_config):
        result = runner.invoke(cli, ["export", "systemd", "api"])
        data = json.loads(result.output)
        assert data["success"] is True
        unit = data["data"]["unit"]
        assert "[Unit]" in unit
        assert "[Service]" in unit
        assert "[Install]" in unit
        assert "ExecStart=" in unit

    def test_export_systemd_all(self, runner, sample_config):
        result = runner.invoke(cli, ["export", "systemd", "--all"])
        data = json.loads(result.output)
        assert data["success"] is True
        assert data["data"]["count"] >= 1
        assert "units" in data["data"]


# ---------------------------------------------------------------------------
# [C11] Export compose generates valid docker-compose.yml
# ---------------------------------------------------------------------------


class TestC11ExportCompose:
    """[C11] Export produces valid docker-compose content."""

    def test_export_compose_has_services(self, runner, sample_config):
        result = runner.invoke(cli, ["export", "compose"])
        data = json.loads(result.output)
        assert data["success"] is True
        compose = data["data"]["compose"]
        assert "services:" in compose


# ---------------------------------------------------------------------------
# [C12] Import Procfile creates process definitions
# ---------------------------------------------------------------------------


class TestC12ImportProcfile:
    """[C12] Procfile import creates correct process definitions."""

    def test_import_procfile_dry_run(self, runner, config_dir, tmp_path):
        procfile = tmp_path / "Procfile"
        procfile.write_text("web: uvicorn main:app\nworker: celery -A app worker\n")
        result = runner.invoke(cli, ["import", "procfile", str(procfile), "--dry-run"])
        data = json.loads(result.output)
        assert data["success"] is True
        assert data["data"]["dry_run"] is True
        assert data["data"]["count"] == 2
        names = [p["name"] for p in data["data"]["processes"]]
        assert "web" in names
        assert "worker" in names

    def test_import_procfile_writes_config(self, runner, tmp_path):
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        config_loader.reset_config_cache()
        try:
            # Create .procler dir so config can be written
            (tmp_path / ".procler").mkdir()
            procfile = tmp_path / "Procfile"
            procfile.write_text("web: python app.py\n")
            result = runner.invoke(cli, ["import", "procfile", str(procfile)])
            data = json.loads(result.output)
            assert data["success"] is True
            assert data["data"]["imported"] == 1
            assert (tmp_path / ".procler" / "config.yaml").exists()
        finally:
            os.chdir(old_cwd)
            config_loader.reset_config_cache()


# ---------------------------------------------------------------------------
# [C13] CLI list --namespace filters correctly
# ---------------------------------------------------------------------------


class TestC13NamespaceFilter:
    """[C13] procler list --namespace filters processes by namespace."""

    def test_namespace_filter(self, runner):
        runner.invoke(cli, ["define", "--name", "a", "--command", "sleep 1"])
        result = runner.invoke(cli, ["list", "--namespace", "nonexistent-ns"])
        data = json.loads(result.output)
        assert data["success"] is True
        # Process 'a' is in 'default' namespace, so filtering by another should exclude it
        assert len(data["data"]["processes"]) == 0


# ---------------------------------------------------------------------------
# [C14] CLI list --resolve substitutes variables
# ---------------------------------------------------------------------------


class TestC14ListResolve:
    """[C14] procler list --resolve substitutes ${VAR} in commands."""

    def test_resolve_flag_available(self, runner):
        """The --resolve flag is accepted by the list command."""
        result = runner.invoke(cli, ["list", "--resolve"])
        data = json.loads(result.output)
        assert data["success"] is True


# ---------------------------------------------------------------------------
# [C15] Idempotent start (start running = no-op)
# ---------------------------------------------------------------------------


class TestC15IdempotentStart:
    """[C15] Starting an already-running process is a no-op."""

    def test_start_already_running(self, runner):
        # Define
        define_result = runner.invoke(cli, ["define", "--name", "idem", "--command", "sleep 30"])
        assert json.loads(define_result.output)["success"] is True

        # First start
        start1 = runner.invoke(cli, ["start", "idem"])
        start1_data = json.loads(start1.output)
        assert start1_data["success"] is True, f"First start failed: {start1.output}"
        pid1 = start1_data["data"]["process"]["pid"]

        # Second start should be idempotent
        start2 = runner.invoke(cli, ["start", "idem"])
        data2 = json.loads(start2.output)
        assert data2["success"] is True
        assert data2["data"]["status"] == "already_running"
        assert data2["data"]["process"]["pid"] == pid1

        runner.invoke(cli, ["stop", "idem"])


# ---------------------------------------------------------------------------
# [C16] Idempotent stop (stop stopped = no-op)
# ---------------------------------------------------------------------------


class TestC16IdempotentStop:
    """[C16] Stopping an already-stopped process is a no-op."""

    def test_stop_already_stopped(self, runner):
        runner.invoke(cli, ["define", "--name", "idem", "--command", "sleep 30"])
        result = runner.invoke(cli, ["stop", "idem"])
        data = json.loads(result.output)
        assert data["success"] is True
        assert data["data"]["status"] == "already_stopped"
