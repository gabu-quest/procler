"""Tests for namespace isolation feature."""

import json

from click.testing import CliRunner

from procler.cli import cli
from procler.config.schema import ProcessDef
from procler.models import Process


class TestProcessDefNamespace:
    """Test namespace field on ProcessDef."""

    def test_namespace_default(self):
        """ProcessDef defaults namespace to 'default'."""
        proc = ProcessDef(command="echo hello")
        assert proc.namespace == "default"

    def test_namespace_custom(self):
        """ProcessDef accepts custom namespace."""
        proc = ProcessDef(command="echo hello", namespace="project-a")
        assert proc.namespace == "project-a"


class TestProcessModelNamespace:
    """Test namespace field on Process model."""

    def test_model_default_namespace(self):
        """Process model defaults namespace to 'default'."""
        process = Process(name="test", command="echo hello")
        process.save()

        loaded = Process.from_id(process._id)
        assert loaded.namespace == "default"

    def test_model_custom_namespace(self):
        """Process model stores custom namespace."""
        process = Process(name="test", command="echo hello", namespace="project-a")
        process.save()

        loaded = Process.from_id(process._id)
        assert loaded.namespace == "project-a"

    def test_filter_by_namespace(self):
        """Can filter processes by namespace."""
        from sqler.query import SQLerField as F

        Process(name="api-a", command="app", namespace="project-a").save()
        Process(name="api-b", command="app", namespace="project-b").save()
        Process(name="worker-a", command="worker", namespace="project-a").save()

        project_a = Process.query().filter(F("namespace") == "project-a").all()
        assert len(project_a) == 2
        names = {p.name for p in project_a}
        assert names == {"api-a", "worker-a"}

        project_b = Process.query().filter(F("namespace") == "project-b").all()
        assert len(project_b) == 1
        assert project_b[0].name == "api-b"


class TestNamespaceConfigParsing:
    """Test namespace in YAML config."""

    def test_config_with_namespace(self, tmp_path):
        """Config file with namespace parses correctly."""
        import os

        from procler.config import loader as config_loader

        config_dir = tmp_path / ".procler"
        config_dir.mkdir()
        (config_dir / "config.yaml").write_text("""
version: 1

processes:
  api:
    command: uvicorn main:app
    namespace: project-a
  worker:
    command: celery worker
""")

        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        config_loader.reset_config_cache()

        try:
            from procler.config import get_config

            config = get_config()
            assert config.processes["api"].namespace == "project-a"
            assert config.processes["worker"].namespace == "default"
        finally:
            os.chdir(old_cwd)
            config_loader.reset_config_cache()


class TestNamespaceCLI:
    """Test CLI namespace filtering."""

    def test_list_all_namespaces(self):
        """List without --namespace shows all processes."""
        Process(name="api-a", command="app", namespace="project-a").save()
        Process(name="api-b", command="app", namespace="project-b").save()

        runner = CliRunner()
        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0

        data = json.loads(result.output)
        assert data["success"] is True
        assert len(data["data"]["processes"]) == 2

    def test_list_filtered_by_namespace(self):
        """List with --namespace filters to that namespace."""
        Process(name="api-a", command="app", namespace="project-a").save()
        Process(name="api-b", command="app", namespace="project-b").save()
        Process(name="worker-a", command="worker", namespace="project-a").save()

        runner = CliRunner()
        result = runner.invoke(cli, ["list", "--namespace", "project-a"])
        assert result.exit_code == 0

        data = json.loads(result.output)
        assert data["success"] is True
        assert len(data["data"]["processes"]) == 2
        names = {p["name"] for p in data["data"]["processes"]}
        assert names == {"api-a", "worker-a"}

    def test_list_namespace_includes_field(self):
        """List output includes namespace field."""
        Process(name="api", command="app", namespace="myns").save()

        runner = CliRunner()
        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0

        data = json.loads(result.output)
        assert data["data"]["processes"][0]["namespace"] == "myns"
