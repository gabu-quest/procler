"""Tests for export to systemd and Docker Compose."""

from procler.config.schema import (
    ContextType,
    DependencyCondition,
    DependencyDef,
    HealthCheckDef,
    ProcessDef,
)
from procler.core.export import export_compose, export_systemd_unit


class TestExportSystemd:
    """Test systemd unit file generation."""

    def test_basic_unit(self):
        """Generate a basic systemd unit for a simple process."""
        proc = ProcessDef(command="uvicorn main:app --port 8000")
        unit = export_systemd_unit("api", proc)

        assert "[Unit]" in unit
        assert "[Service]" in unit
        assert "[Install]" in unit
        assert "ExecStart=uvicorn main:app --port 8000" in unit
        assert "Type=simple" in unit
        assert "Restart=on-failure" in unit
        assert "WantedBy=multi-user.target" in unit

    def test_unit_with_cwd(self):
        """systemd unit includes WorkingDirectory when cwd is set."""
        proc = ProcessDef(command="python app.py", cwd="/opt/myapp")
        unit = export_systemd_unit("myapp", proc)

        assert "WorkingDirectory=/opt/myapp" in unit

    def test_unit_without_cwd(self):
        """systemd unit omits WorkingDirectory when cwd is not set."""
        proc = ProcessDef(command="echo hello")
        unit = export_systemd_unit("test", proc)

        assert "WorkingDirectory" not in unit

    def test_unit_with_description(self):
        """systemd unit uses process description."""
        proc = ProcessDef(command="app", description="My API server")
        unit = export_systemd_unit("api", proc)

        assert "Description=My API server" in unit

    def test_unit_description_override(self):
        """systemd unit uses override description over process description."""
        proc = ProcessDef(command="app", description="Original")
        unit = export_systemd_unit("api", proc, description="Override")

        assert "Description=Override" in unit
        assert "Description=Original" not in unit

    def test_unit_default_description(self):
        """systemd unit has sensible default description."""
        proc = ProcessDef(command="app")
        unit = export_systemd_unit("api", proc)

        assert "Description=Procler: api" in unit

    def test_unit_with_max_memory(self):
        """systemd unit includes MemoryMax when max_memory is set."""
        proc = ProcessDef(command="app", max_memory="512M")
        unit = export_systemd_unit("api", proc)

        assert "MemoryMax=512M" in unit

    def test_unit_without_max_memory(self):
        """systemd unit omits MemoryMax when not set."""
        proc = ProcessDef(command="app")
        unit = export_systemd_unit("api", proc)

        assert "MemoryMax" not in unit


class TestExportCompose:
    """Test Docker Compose YAML generation."""

    def test_basic_compose(self):
        """Generate compose for simple processes."""
        processes = {
            "api": ProcessDef(command="uvicorn main:app"),
            "worker": ProcessDef(command="celery worker"),
        }
        compose = export_compose(processes)

        assert "services:" in compose
        assert "  api:" in compose
        assert "    command: uvicorn main:app" in compose
        assert "  worker:" in compose
        assert "    command: celery worker" in compose

    def test_compose_with_project_name(self):
        """Compose includes project name when specified."""
        processes = {"api": ProcessDef(command="app")}
        compose = export_compose(processes, project_name="myproject")

        assert "name: myproject" in compose

    def test_compose_with_container_name(self):
        """Compose includes container_name for docker context processes."""
        processes = {
            "db": ProcessDef(
                command="postgres",
                context=ContextType.DOCKER,
                container="my-postgres",
            ),
        }
        compose = export_compose(processes)

        assert "container_name: my-postgres" in compose

    def test_compose_with_working_dir(self):
        """Compose includes working_dir when cwd is set."""
        processes = {
            "api": ProcessDef(command="app", cwd="/opt/app"),
        }
        compose = export_compose(processes)

        assert "working_dir: /opt/app" in compose

    def test_compose_with_depends_on(self):
        """Compose maps depends_on with conditions."""
        processes = {
            "db": ProcessDef(command="postgres"),
            "api": ProcessDef(
                command="app",
                depends_on=[
                    DependencyDef(name="db", condition=DependencyCondition.HEALTHY),
                ],
            ),
        }
        compose = export_compose(processes)

        assert "depends_on:" in compose
        assert "db:" in compose
        assert "condition: service_healthy" in compose

    def test_compose_with_started_dependency(self):
        """Compose maps started dependency to service_started."""
        processes = {
            "db": ProcessDef(command="postgres"),
            "api": ProcessDef(
                command="app",
                depends_on=["db"],
            ),
        }
        compose = export_compose(processes)

        assert "condition: service_started" in compose

    def test_compose_with_healthcheck_command(self):
        """Compose maps command-based health check."""
        processes = {
            "api": ProcessDef(
                command="app",
                healthcheck=HealthCheckDef(
                    test="curl -f http://localhost/health",
                    interval="10s",
                    timeout="5s",
                    retries=3,
                ),
            ),
        }
        compose = export_compose(processes)

        assert "healthcheck:" in compose
        assert "curl -f http://localhost/health" in compose
        assert "interval: 10s" in compose
        assert "timeout: 5s" in compose
        assert "retries: 3" in compose

    def test_compose_with_http_healthcheck(self):
        """Compose converts http_get probe to curl command."""
        processes = {
            "api": ProcessDef(
                command="app",
                healthcheck=HealthCheckDef(
                    http_get="http://localhost:8000/health",
                ),
            ),
        }
        compose = export_compose(processes)

        assert "curl -f http://localhost:8000/health" in compose

    def test_compose_with_tcp_healthcheck(self):
        """Compose converts tcp_socket probe to nc command."""
        processes = {
            "db": ProcessDef(
                command="postgres",
                healthcheck=HealthCheckDef(
                    tcp_socket="localhost:5432",
                ),
            ),
        }
        compose = export_compose(processes)

        assert "nc -z localhost 5432" in compose

    def test_compose_with_max_memory(self):
        """Compose includes deploy.resources.limits.memory."""
        processes = {
            "api": ProcessDef(command="app", max_memory="512M"),
        }
        compose = export_compose(processes)

        assert "memory: 512M" in compose

    def test_compose_with_tags_as_labels(self):
        """Compose maps tags to labels."""
        processes = {
            "api": ProcessDef(command="app", tags=["backend", "api"]),
        }
        compose = export_compose(processes)

        assert "labels:" in compose
        assert "procler.tag.backend" in compose
        assert "procler.tag.api" in compose

    def test_compose_description_as_comment(self):
        """Compose includes description as YAML comment."""
        processes = {
            "api": ProcessDef(command="app", description="My API"),
        }
        compose = export_compose(processes)

        assert "# My API" in compose


class TestExportCLI:
    """Test export CLI commands."""

    def test_export_systemd_cli(self, tmp_path):
        """CLI export systemd command produces valid output."""
        import json
        import os

        from click.testing import CliRunner

        from procler.cli import cli
        from procler.config import loader as config_loader

        config_dir = tmp_path / ".procler"
        config_dir.mkdir()
        (config_dir / "config.yaml").write_text("""
version: 1

processes:
  api:
    command: uvicorn main:app
    description: API server
    cwd: /opt/api
""")

        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        config_loader.reset_config_cache()

        try:
            runner = CliRunner()
            result = runner.invoke(cli, ["export", "systemd", "api"])
            assert result.exit_code == 0

            data = json.loads(result.output)
            assert data["success"] is True
            assert "ExecStart=uvicorn main:app" in data["data"]["unit"]
            assert "WorkingDirectory=/opt/api" in data["data"]["unit"]
        finally:
            os.chdir(old_cwd)
            config_loader.reset_config_cache()

    def test_export_systemd_all_cli(self, tmp_path):
        """CLI export systemd --all produces units for all local processes."""
        import json
        import os

        from click.testing import CliRunner

        from procler.cli import cli
        from procler.config import loader as config_loader

        config_dir = tmp_path / ".procler"
        config_dir.mkdir()
        (config_dir / "config.yaml").write_text("""
version: 1

processes:
  api:
    command: uvicorn main:app
  worker:
    command: celery worker
  db:
    command: postgres
    context: docker
    container: my-postgres
""")

        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        config_loader.reset_config_cache()

        try:
            runner = CliRunner()
            result = runner.invoke(cli, ["export", "systemd", "--all"])
            assert result.exit_code == 0

            data = json.loads(result.output)
            assert data["success"] is True
            # Only local processes should be exported
            assert "api" in data["data"]["units"]
            assert "worker" in data["data"]["units"]
            assert "db" not in data["data"]["units"]  # Docker process excluded
            assert data["data"]["count"] == 2
        finally:
            os.chdir(old_cwd)
            config_loader.reset_config_cache()

    def test_export_compose_cli(self, tmp_path):
        """CLI export compose command produces valid output."""
        import json
        import os

        from click.testing import CliRunner

        from procler.cli import cli
        from procler.config import loader as config_loader

        config_dir = tmp_path / ".procler"
        config_dir.mkdir()
        (config_dir / "config.yaml").write_text("""
version: 1

processes:
  api:
    command: uvicorn main:app
  worker:
    command: celery worker
""")

        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        config_loader.reset_config_cache()

        try:
            runner = CliRunner()
            result = runner.invoke(cli, ["export", "compose"])
            assert result.exit_code == 0

            data = json.loads(result.output)
            assert data["success"] is True
            assert "services:" in data["data"]["compose"]
        finally:
            os.chdir(old_cwd)
            config_loader.reset_config_cache()
