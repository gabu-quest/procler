"""Procler TUI application."""

from __future__ import annotations

import asyncio
from typing import Any

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import DataTable, Footer, Header, RichLog, Static

from ..core.events import EVENT_LOG_ENTRY, EVENT_STATUS_CHANGE, get_event_bus
from ..core.process_manager import get_process_manager
from ..db import init_database


class ProcessList(DataTable):
    """Process list table with status indicators."""

    BINDINGS = [
        Binding("s", "start_process", "Start"),
        Binding("x", "stop_process", "Stop"),
        Binding("r", "restart_process", "Restart"),
    ]

    def on_mount(self) -> None:
        self.add_columns("Name", "Status", "PID", "Uptime", "Namespace")
        self.cursor_type = "row"


class LogViewer(RichLog):
    """Live log viewer for selected process."""

    pass


class StatusBar(Static):
    """Bottom status bar showing selected process info."""

    process_name: reactive[str] = reactive("")

    def render(self) -> str:
        if self.process_name:
            return f" Selected: {self.process_name} | [s]tart [x]stop [r]estart"
        return " No process selected | Navigate with arrow keys"


class ProclerTUI(App):
    """Procler Terminal User Interface."""

    TITLE = "Procler"
    SUB_TITLE = "Process Manager"
    CSS = """
    Screen {
        layout: vertical;
    }

    #main-container {
        layout: horizontal;
        height: 1fr;
    }

    #process-list-container {
        width: 50%;
        height: 100%;
        border: solid $accent;
    }

    #log-container {
        width: 50%;
        height: 100%;
        border: solid $accent;
    }

    #log-title {
        dock: top;
        height: 1;
        background: $accent;
        color: $text;
        text-align: center;
    }

    ProcessList {
        height: 1fr;
    }

    LogViewer {
        height: 1fr;
    }

    StatusBar {
        dock: bottom;
        height: 1;
        background: $surface;
        color: $text;
    }

    #list-title {
        dock: top;
        height: 1;
        background: $accent;
        color: $text;
        text-align: center;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("f5", "refresh", "Refresh"),
        Binding("slash", "filter", "Filter"),
    ]

    selected_process: reactive[str | None] = reactive(None)

    def __init__(self) -> None:
        super().__init__()
        self._pm = None
        self._event_bus = None
        self._refresh_task: asyncio.Task | None = None
        self._process_rows: dict[str, str] = {}  # name -> row_key

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main-container"):
            with Vertical(id="process-list-container"):
                yield Static("Processes", id="list-title")
                yield ProcessList(id="process-list")
            with Vertical(id="log-container"):
                yield Static("Logs", id="log-title")
                yield LogViewer(id="log-viewer", highlight=True, markup=True)
        yield StatusBar(id="status-bar")
        yield Footer()

    async def on_mount(self) -> None:
        init_database()
        self._pm = get_process_manager()
        self._event_bus = get_event_bus()

        # Subscribe to events
        self._event_bus.subscribe(EVENT_STATUS_CHANGE, self._on_status_change)
        self._event_bus.subscribe(EVENT_LOG_ENTRY, self._on_log_entry)

        # Initial load
        await self._load_processes()

        # Start periodic refresh
        self._start_refresh_loop()

    def _start_refresh_loop(self) -> None:
        """Start periodic status refresh."""
        self.set_interval(3.0, self._refresh_processes)

    @work(thread=False)
    async def _refresh_processes(self) -> None:
        """Refresh process statuses periodically."""
        await self._load_processes()

    async def _load_processes(self) -> None:
        """Load all processes and update the table."""
        if self._pm is None:
            return

        result = await self._pm.status()
        if not result.get("success"):
            return

        table: ProcessList = self.query_one("#process-list", ProcessList)
        processes = result.get("data", {}).get("processes", [])

        # Track which processes we've seen
        seen_names: set[str] = set()

        for proc in processes:
            name = proc.get("name", "?")
            status = proc.get("status", "unknown")
            pid = str(proc.get("pid") or "-")
            uptime = self._format_uptime(proc.get("uptime_seconds"))
            namespace = proc.get("namespace", "default")
            seen_names.add(name)

            status_display = self._status_icon(status) + " " + status

            if name in self._process_rows:
                # Update existing row
                row_key = self._process_rows[name]
                try:
                    table.update_cell(row_key, "Name", name)
                    table.update_cell(row_key, "Status", status_display)
                    table.update_cell(row_key, "PID", pid)
                    table.update_cell(row_key, "Uptime", uptime)
                    table.update_cell(row_key, "Namespace", namespace)
                except Exception:
                    pass
            else:
                # Add new row
                row_key = table.add_row(name, status_display, pid, uptime, namespace, key=name)
                self._process_rows[name] = name

        # Remove rows for processes that no longer exist
        for name in list(self._process_rows.keys()):
            if name not in seen_names:
                try:
                    table.remove_row(name)
                except Exception:
                    pass
                del self._process_rows[name]

    def _status_icon(self, status: str) -> str:
        """Get a status indicator character."""
        icons = {
            "running": "[green]●[/green]",
            "stopped": "[red]●[/red]",
            "starting": "[yellow]●[/yellow]",
            "stopping": "[yellow]●[/yellow]",
            "error": "[red]✗[/red]",
            "unknown": "[dim]○[/dim]",
        }
        return icons.get(status, "[dim]○[/dim]")

    def _format_uptime(self, seconds: float | None) -> str:
        """Format uptime seconds into human-readable string."""
        if seconds is None:
            return "-"
        seconds = int(seconds)
        if seconds < 60:
            return f"{seconds}s"
        if seconds < 3600:
            return f"{seconds // 60}m {seconds % 60}s"
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"

    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection in process list."""
        table: ProcessList = self.query_one("#process-list", ProcessList)
        row_key = event.row_key

        # Get the process name from the first column
        name = table.get_cell(row_key, "Name")
        self.selected_process = name

        # Update status bar
        status_bar: StatusBar = self.query_one("#status-bar", StatusBar)
        status_bar.process_name = name

        # Update log title
        log_title: Static = self.query_one("#log-title", Static)
        log_title.update(f"Logs: {name}")

        # Load logs for selected process
        await self._load_logs(name)

    async def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Handle row highlight (cursor movement) in process list."""
        if event.row_key is None:
            return

        table: ProcessList = self.query_one("#process-list", ProcessList)
        try:
            name = table.get_cell(event.row_key, "Name")
        except Exception:
            return

        self.selected_process = name

        # Update status bar
        status_bar: StatusBar = self.query_one("#status-bar", StatusBar)
        status_bar.process_name = name

        # Update log title
        log_title: Static = self.query_one("#log-title", Static)
        log_title.update(f"Logs: {name}")

        # Load logs for selected process
        await self._load_logs(name)

    async def _load_logs(self, name: str) -> None:
        """Load recent logs for a process."""
        if self._pm is None:
            return

        log_viewer: LogViewer = self.query_one("#log-viewer", LogViewer)
        log_viewer.clear()

        result = await self._pm.logs(name, tail=50)
        if result.get("success"):
            entries = result.get("data", {}).get("logs", [])
            for entry in entries:
                timestamp = entry.get("timestamp", "")
                stream = entry.get("stream", "stdout")
                line = entry.get("line", "")

                if stream == "stderr":
                    log_viewer.write(f"[red]{timestamp}[/red] {line}")
                else:
                    log_viewer.write(f"[dim]{timestamp}[/dim] {line}")

    async def _on_status_change(self, data: dict[str, Any]) -> None:
        """Handle status change events from EventBus."""
        self.call_from_thread(self._refresh_processes)

    async def _on_log_entry(self, data: dict[str, Any]) -> None:
        """Handle log entry events from EventBus."""
        process_name = data.get("process_name")
        if process_name and process_name == self.selected_process:
            log_viewer: LogViewer = self.query_one("#log-viewer", LogViewer)
            timestamp = data.get("timestamp", "")
            stream = data.get("stream", "stdout")
            line = data.get("line", "")

            if stream == "stderr":
                log_viewer.write(f"[red]{timestamp}[/red] {line}")
            else:
                log_viewer.write(f"[dim]{timestamp}[/dim] {line}")

    async def action_refresh(self) -> None:
        """Manual refresh of process list."""
        await self._load_processes()

    async def action_start_process(self) -> None:
        """Start the selected process."""
        if self.selected_process and self._pm:
            result = await self._pm.start(self.selected_process)
            if result.get("success"):
                self.notify(f"Started {self.selected_process}", severity="information")
            else:
                self.notify(f"Failed: {result.get('error', 'unknown')}", severity="error")
            await self._load_processes()

    async def action_stop_process(self) -> None:
        """Stop the selected process."""
        if self.selected_process and self._pm:
            result = await self._pm.stop(self.selected_process)
            if result.get("success"):
                self.notify(f"Stopped {self.selected_process}", severity="information")
            else:
                self.notify(f"Failed: {result.get('error', 'unknown')}", severity="error")
            await self._load_processes()

    async def action_restart_process(self) -> None:
        """Restart the selected process."""
        if self.selected_process and self._pm:
            result = await self._pm.restart(self.selected_process)
            if result.get("success"):
                self.notify(f"Restarted {self.selected_process}", severity="information")
            else:
                self.notify(f"Failed: {result.get('error', 'unknown')}", severity="error")
            await self._load_processes()

    async def action_filter(self) -> None:
        """Placeholder for filter functionality."""
        self.notify("Filter not yet implemented", severity="warning")


def run_tui() -> None:
    """Launch the Procler TUI."""
    app = ProclerTUI()
    app.run()
