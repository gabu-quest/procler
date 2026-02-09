"""Tests for Procfile import feature."""

import json

import pytest
from click.testing import CliRunner

from procler.cli import cli
from procler.core.import_procfile import generate_config_yaml, parse_procfile, parse_procfile_from_path


class TestParseProcfile:
    """Test Procfile parsing logic."""

    def test_basic_procfile(self):
        """Parse standard Procfile with multiple entries."""
        content = "web: python app.py\nworker: celery worker\n"
        result = parse_procfile(content)

        assert len(result) == 2
        assert result["web"].command == "python app.py"
        assert result["worker"].command == "celery worker"

    def test_comments_ignored(self):
        """Lines starting with # are ignored."""
        content = "# This is a comment\nweb: python app.py\n# Another comment\n"
        result = parse_procfile(content)

        assert len(result) == 1
        assert result["web"].command == "python app.py"

    def test_blank_lines_ignored(self):
        """Blank lines are ignored."""
        content = "\nweb: python app.py\n\n\nworker: celery worker\n\n"
        result = parse_procfile(content)

        assert len(result) == 2

    def test_command_with_colons(self):
        """Commands containing colons parse correctly (only first colon splits)."""
        content = "web: uvicorn main:app --host 0.0.0.0:8000\n"
        result = parse_procfile(content)

        assert len(result) == 1
        assert result["web"].command == "uvicorn main:app --host 0.0.0.0:8000"

    def test_whitespace_handling(self):
        """Leading/trailing whitespace is trimmed."""
        content = "  web :  python app.py  \n"
        result = parse_procfile(content)

        assert len(result) == 1
        assert result["web"].command == "python app.py"

    def test_empty_content(self):
        """Empty Procfile returns empty dict."""
        result = parse_procfile("")
        assert result == {}

    def test_only_comments(self):
        """Procfile with only comments returns empty dict."""
        result = parse_procfile("# just a comment\n# and another\n")
        assert result == {}

    def test_invalid_line_no_colon(self):
        """Line without colon raises ValueError."""
        with pytest.raises(ValueError, match="Invalid Procfile syntax"):
            parse_procfile("web python app.py\n")

    def test_empty_name(self):
        """Empty process name raises ValueError."""
        with pytest.raises(ValueError, match="Empty process name"):
            parse_procfile(": python app.py\n")

    def test_empty_command(self):
        """Empty command raises ValueError."""
        with pytest.raises(ValueError, match="Empty command"):
            parse_procfile("web:\n")

    def test_invalid_name_characters(self):
        """Invalid characters in name raise ValueError."""
        with pytest.raises(ValueError, match="Invalid process name"):
            parse_procfile("web server: python app.py\n")

    def test_duplicate_name(self):
        """Duplicate process names raise ValueError."""
        with pytest.raises(ValueError, match="Duplicate process name"):
            parse_procfile("web: python app.py\nweb: python other.py\n")

    def test_hyphen_underscore_in_name(self):
        """Names with hyphens and underscores are valid."""
        content = "my-web: python app.py\nmy_worker: celery worker\n"
        result = parse_procfile(content)

        assert len(result) == 2
        assert "my-web" in result
        assert "my_worker" in result

    def test_complex_commands(self):
        """Commands with pipes, redirects, and flags parse correctly."""
        content = "web: gunicorn -w 4 -b 0.0.0.0:8000 app:create_app()\n"
        result = parse_procfile(content)

        assert result["web"].command == "gunicorn -w 4 -b 0.0.0.0:8000 app:create_app()"

    def test_default_context_is_local(self):
        """Imported processes default to local context."""
        content = "web: python app.py\n"
        result = parse_procfile(content)

        assert result["web"].context.value == "local"


class TestParseProcfileFromPath:
    """Test Procfile parsing from file path."""

    def test_read_from_file(self, tmp_path):
        """Parse a real Procfile on disk."""
        procfile = tmp_path / "Procfile"
        procfile.write_text("web: python app.py\nworker: celery worker\n")

        result = parse_procfile_from_path(procfile)

        assert len(result) == 2
        assert result["web"].command == "python app.py"
        assert result["worker"].command == "celery worker"

    def test_file_not_found(self, tmp_path):
        """Missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="Procfile not found"):
            parse_procfile_from_path(tmp_path / "nonexistent")


class TestGenerateConfigYaml:
    """Test YAML config generation."""

    def test_basic_generation(self):
        """Generate config from parsed processes."""
        from procler.config.schema import ProcessDef

        processes = {
            "web": ProcessDef(command="python app.py"),
            "worker": ProcessDef(command="celery worker"),
        }

        yaml_str = generate_config_yaml(processes)

        assert "version: 1" in yaml_str
        assert "web:" in yaml_str
        assert "command: python app.py" in yaml_str
        assert "worker:" in yaml_str
        assert "command: celery worker" in yaml_str

    def test_merge_with_existing(self):
        """Merge new processes into existing config."""
        from procler.config.schema import ProcessDef

        existing = {
            "version": 1,
            "processes": {
                "db": {"command": "postgres"},
            },
        }
        new_processes = {
            "web": ProcessDef(command="python app.py"),
        }

        yaml_str = generate_config_yaml(new_processes, existing)

        assert "db:" in yaml_str
        assert "command: postgres" in yaml_str
        assert "web:" in yaml_str
        assert "command: python app.py" in yaml_str

    def test_empty_processes(self):
        """Generate config with no processes."""
        yaml_str = generate_config_yaml({})

        assert "version: 1" in yaml_str
        assert "processes:" in yaml_str


class TestImportProcfileCLI:
    """Test CLI import procfile command."""

    def test_dry_run(self, tmp_path):
        """Dry run shows preview without writing."""
        procfile = tmp_path / "Procfile"
        procfile.write_text("web: python app.py\nworker: celery worker\n")

        runner = CliRunner()
        result = runner.invoke(cli, ["import", "procfile", str(procfile), "--dry-run"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["success"] is True
        assert data["data"]["dry_run"] is True
        assert data["data"]["count"] == 2
        assert len(data["data"]["processes"]) == 2

        names = {p["name"] for p in data["data"]["processes"]}
        assert names == {"web", "worker"}

        # Config file should NOT be written
        config_path = tmp_path / ".procler" / "config.yaml"
        assert not config_path.exists()

    def test_import_writes_config(self, tmp_path, monkeypatch):
        """Import writes config.yaml to .procler directory."""
        procfile = tmp_path / "Procfile"
        procfile.write_text("web: python app.py\n")

        # Make find_config_dir return tmp_path/.procler
        config_dir = tmp_path / ".procler"
        monkeypatch.setattr("procler.config.loader.find_config_dir", lambda start_dir=None: config_dir)
        monkeypatch.setattr("procler.config.find_config_dir", lambda start_dir=None: config_dir)

        runner = CliRunner()
        result = runner.invoke(cli, ["import", "procfile", str(procfile)])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["success"] is True
        assert data["data"]["imported"] == 1

        # Config file should exist
        assert config_dir.exists()
        config_content = (config_dir / "config.yaml").read_text()
        assert "web:" in config_content
        assert "command: python app.py" in config_content

    def test_import_invalid_procfile(self, tmp_path):
        """Import with invalid Procfile returns error."""
        procfile = tmp_path / "Procfile"
        procfile.write_text("this has no colon separator\n")

        runner = CliRunner()
        result = runner.invoke(cli, ["import", "procfile", str(procfile)])

        assert result.exit_code != 0
        data = json.loads(result.output)
        assert data["success"] is False
        assert data["error_code"] == "parse_error"

    def test_import_empty_procfile(self, tmp_path):
        """Import with empty Procfile returns error."""
        procfile = tmp_path / "Procfile"
        procfile.write_text("# only comments\n")

        runner = CliRunner()
        result = runner.invoke(cli, ["import", "procfile", str(procfile)])

        assert result.exit_code != 0
        data = json.loads(result.output)
        assert data["success"] is False
        assert data["error_code"] == "empty_procfile"

    def test_import_nonexistent_file(self):
        """Import with nonexistent file fails."""
        runner = CliRunner()
        result = runner.invoke(cli, ["import", "procfile", "/nonexistent/Procfile"])

        # Click handles exists=True validation before our code
        assert result.exit_code != 0
