"""Tests for TUI mode (Phase 9)."""

from unittest.mock import AsyncMock, patch

from click.testing import CliRunner
from textual.widgets import DataTable

from procler.cli import cli
from procler.tui.app import ProclerTUI, run_tui


class TestTUIApp:
    """Test TUI application structure."""

    async def test_app_creates_widgets(self):
        """TUI app creates all expected widgets."""
        app = ProclerTUI()
        async with app.run_test(size=(120, 40)):
            # Check main widgets exist
            process_list = app.query_one("#process-list", DataTable)
            assert process_list is not None

            log_viewer = app.query_one("#log-viewer")
            assert log_viewer is not None

            status_bar = app.query_one("#status-bar")
            assert status_bar is not None

    async def test_process_list_has_columns(self):
        """Process list table has correct columns."""
        app = ProclerTUI()
        async with app.run_test(size=(120, 40)):
            table = app.query_one("#process-list", DataTable)
            column_labels = [col.label.plain for col in table.columns.values()]
            assert "Name" in column_labels
            assert "Status" in column_labels
            assert "PID" in column_labels
            assert "Uptime" in column_labels
            assert "Namespace" in column_labels

    async def test_initial_log_title(self):
        """Log panel starts with generic title."""
        app = ProclerTUI()
        async with app.run_test(size=(120, 40)):
            log_title = app.query_one("#log-title")
            assert "Logs" in str(log_title.render())

    async def test_status_bar_default(self):
        """Status bar shows default message when no process selected."""
        app = ProclerTUI()
        async with app.run_test(size=(120, 40)):
            status_bar = app.query_one("#status-bar")
            rendered = str(status_bar.render())
            assert "No process selected" in rendered

    async def test_quit_binding(self):
        """Pressing q quits the app."""
        app = ProclerTUI()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.press("q")
            assert app.return_code is not None or not app.is_running


class TestTUIHelpers:
    """Test TUI helper methods."""

    def test_format_uptime_seconds(self):
        """Format short uptime."""
        app = ProclerTUI()
        assert app._format_uptime(45) == "45s"

    def test_format_uptime_minutes(self):
        """Format minute-range uptime."""
        app = ProclerTUI()
        assert app._format_uptime(125) == "2m 5s"

    def test_format_uptime_hours(self):
        """Format hour-range uptime."""
        app = ProclerTUI()
        assert app._format_uptime(7265) == "2h 1m"

    def test_format_uptime_none(self):
        """Format None uptime."""
        app = ProclerTUI()
        assert app._format_uptime(None) == "-"

    def test_status_icon_running(self):
        """Running status gets green icon."""
        app = ProclerTUI()
        icon = app._status_icon("running")
        assert "green" in icon

    def test_status_icon_stopped(self):
        """Stopped status gets red icon."""
        app = ProclerTUI()
        icon = app._status_icon("stopped")
        assert "red" in icon

    def test_status_icon_unknown(self):
        """Unknown status gets dim icon."""
        app = ProclerTUI()
        icon = app._status_icon("unknown")
        assert "dim" in icon

    def test_status_icon_starting(self):
        """Starting status gets yellow icon."""
        app = ProclerTUI()
        icon = app._status_icon("starting")
        assert "yellow" in icon


class TestTUIProcessLoading:
    """Test process data loading in TUI."""

    async def test_loads_processes_on_mount(self):
        """TUI loads process list on mount."""
        mock_status = {
            "success": True,
            "data": {
                "processes": [
                    {
                        "name": "api",
                        "status": "running",
                        "pid": 1234,
                        "uptime_seconds": 60,
                        "namespace": "default",
                    },
                    {
                        "name": "worker",
                        "status": "stopped",
                        "pid": None,
                        "uptime_seconds": None,
                        "namespace": "default",
                    },
                ]
            },
        }

        with patch("procler.tui.app.get_process_manager") as mock_get_pm:
            mock_pm = AsyncMock()
            mock_pm.status.return_value = mock_status
            mock_get_pm.return_value = mock_pm

            app = ProclerTUI()
            async with app.run_test(size=(120, 40)) as pilot:
                await pilot.pause()

                table = app.query_one("#process-list", DataTable)
                assert table.row_count == 2

    async def test_loads_logs_on_select(self):
        """Selecting a process loads its logs."""
        mock_status = {
            "success": True,
            "data": {
                "processes": [
                    {
                        "name": "api",
                        "status": "running",
                        "pid": 1234,
                        "uptime_seconds": 60,
                        "namespace": "default",
                    },
                ]
            },
        }
        mock_logs = {
            "success": True,
            "data": {
                "logs": [
                    {"timestamp": "2026-01-01T00:00:00", "stream": "stdout", "line": "Server started"},
                ]
            },
        }

        with patch("procler.tui.app.get_process_manager") as mock_get_pm:
            mock_pm = AsyncMock()
            mock_pm.status.return_value = mock_status
            mock_pm.logs.return_value = mock_logs
            mock_get_pm.return_value = mock_pm

            app = ProclerTUI()
            async with app.run_test(size=(120, 40)) as pilot:
                await pilot.pause()

                table = app.query_one("#process-list", DataTable)
                assert table.row_count == 1

                # Directly call _load_logs to verify log fetching works
                await app._load_logs("api")
                mock_pm.logs.assert_called_with("api", tail=50)


class TestTUICLI:
    """Test CLI tui command."""

    def test_tui_command_exists(self):
        """The tui command is registered."""
        runner = CliRunner()
        result = runner.invoke(cli, ["tui", "--help"])
        assert result.exit_code == 0
        assert "Terminal User Interface" in result.output

    def test_tui_run_function_exists(self):
        """The run_tui function is importable."""
        assert callable(run_tui)
