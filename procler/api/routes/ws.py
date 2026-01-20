"""WebSocket handler for real-time updates."""

import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ...core.events import EVENT_LOG_ENTRY, EVENT_RECIPE_STEP, EVENT_STATUS_CHANGE, get_event_bus
from ...core.log_tailer import get_log_tailer
from ...core.process_manager import get_linux_process_state
from ...db import init_database
from ...models import Process

logger = logging.getLogger(__name__)

router = APIRouter()
STATUS_POLL_INTERVAL = 5.0


class ConnectionManager:
    """Manages WebSocket connections and subscriptions."""

    def __init__(self):
        # All active connections
        self.active_connections: list[WebSocket] = []
        # Process-specific log subscriptions: process_id -> set of websockets
        self.log_subscriptions: dict[int, set[WebSocket]] = {}
        # Process-specific status subscriptions: process_id -> set of websockets
        self.status_subscriptions: dict[int, set[WebSocket]] = {}
        # Global status subscriptions (all process changes)
        self.global_status_subscriptions: set[WebSocket] = set()
        # Status pollers to refresh linux_state in real time
        self.status_pollers: dict[WebSocket, asyncio.Task] = {}
        # Recipe subscriptions: recipe_name -> set of websockets
        self.recipe_subscriptions: dict[str, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket) -> None:
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection and all its subscriptions."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        poller = self.status_pollers.pop(websocket, None)
        if poller:
            poller.cancel()

        # Track which processes need tailer cleanup
        processes_to_check: list[int] = []

        # Remove from all log subscriptions
        for process_id in list(self.log_subscriptions.keys()):
            self.log_subscriptions[process_id].discard(websocket)
            if not self.log_subscriptions[process_id]:
                del self.log_subscriptions[process_id]
                processes_to_check.append(process_id)

        # Remove from all status subscriptions
        for process_id in list(self.status_subscriptions.keys()):
            self.status_subscriptions[process_id].discard(websocket)
            if not self.status_subscriptions[process_id]:
                del self.status_subscriptions[process_id]

        # Remove from global subscriptions
        self.global_status_subscriptions.discard(websocket)

        # Remove from recipe subscriptions
        for recipe_name in list(self.recipe_subscriptions.keys()):
            self.recipe_subscriptions[recipe_name].discard(websocket)
            if not self.recipe_subscriptions[recipe_name]:
                del self.recipe_subscriptions[recipe_name]

        # Stop tailers for processes with no remaining subscribers
        for process_id in processes_to_check:
            await self._stop_tailing_if_needed(process_id)

    async def subscribe_logs(self, websocket: WebSocket, process_id: int) -> None:
        """Subscribe to log updates for a specific process."""
        is_first_subscriber = process_id not in self.log_subscriptions

        if process_id not in self.log_subscriptions:
            self.log_subscriptions[process_id] = set()
        self.log_subscriptions[process_id].add(websocket)

        # Start tailing if this is the first subscriber for a daemon process
        if is_first_subscriber:
            await self._start_tailing_if_needed(process_id)

    async def unsubscribe_logs(self, websocket: WebSocket, process_id: int) -> None:
        """Unsubscribe from log updates for a specific process."""
        if process_id in self.log_subscriptions:
            self.log_subscriptions[process_id].discard(websocket)
            if not self.log_subscriptions[process_id]:
                del self.log_subscriptions[process_id]
                # Stop tailing when no more subscribers
                await self._stop_tailing_if_needed(process_id)

    async def _start_tailing_if_needed(self, process_id: int) -> None:
        """Start log file tailing if the process has a log file."""
        try:
            init_database()
            process = Process.from_id(process_id)
            if process and getattr(process, "log_file", None):
                tailer = get_log_tailer()
                started = await tailer.start_tailing(process)
                if started:
                    logger.info(f"Started tailing logs for process {process.name} (id={process_id})")
            elif process:
                logger.debug(f"Process {process.name} has no log_file configured, skipping tail")
        except Exception as e:
            logger.warning(f"Error starting tailer for process {process_id}: {e}")

    async def _stop_tailing_if_needed(self, process_id: int) -> None:
        """Stop log file tailing when no subscribers remain."""
        try:
            tailer = get_log_tailer()
            await tailer.stop_tailing(process_id)
        except Exception as e:
            logger.debug(f"Error stopping tailer for process {process_id}: {e}")

    def subscribe_status(self, websocket: WebSocket, process_id: int | None = None) -> None:
        """Subscribe to status updates for a specific process or all processes."""
        if process_id is None:
            self.global_status_subscriptions.add(websocket)
        else:
            if process_id not in self.status_subscriptions:
                self.status_subscriptions[process_id] = set()
            self.status_subscriptions[process_id].add(websocket)
        self._ensure_status_poller(websocket)

    def unsubscribe_status(self, websocket: WebSocket, process_id: int | None = None) -> None:
        """Unsubscribe from status updates."""
        if process_id is None:
            self.global_status_subscriptions.discard(websocket)
        elif process_id in self.status_subscriptions:
            self.status_subscriptions[process_id].discard(websocket)
            if not self.status_subscriptions[process_id]:
                del self.status_subscriptions[process_id]
        if not self._has_status_subscription(websocket):
            poller = self.status_pollers.pop(websocket, None)
            if poller:
                poller.cancel()

    async def broadcast_log(self, process_id: int, log_data: dict[str, Any]) -> None:
        """Broadcast a log entry to all subscribers of a process."""
        message = {
            "type": "log",
            "process_id": process_id,
            "data": log_data,
        }
        subscribers = self.log_subscriptions.get(process_id, set())
        await self._send_to_many(subscribers, message)

    async def broadcast_status(self, process_id: int, status_data: dict[str, Any]) -> None:
        """Broadcast a status change to subscribers."""
        message = {
            "type": "status",
            "process_id": process_id,
            "data": status_data,
        }

        # Send to process-specific subscribers
        subscribers = self.status_subscriptions.get(process_id, set())
        # Also send to global subscribers
        all_subscribers = subscribers | self.global_status_subscriptions
        await self._send_to_many(all_subscribers, message)

    def subscribe_recipe(self, websocket: WebSocket, recipe_name: str) -> None:
        """Subscribe to recipe execution updates."""
        if recipe_name not in self.recipe_subscriptions:
            self.recipe_subscriptions[recipe_name] = set()
        self.recipe_subscriptions[recipe_name].add(websocket)

    def unsubscribe_recipe(self, websocket: WebSocket, recipe_name: str) -> None:
        """Unsubscribe from recipe execution updates."""
        if recipe_name in self.recipe_subscriptions:
            self.recipe_subscriptions[recipe_name].discard(websocket)
            if not self.recipe_subscriptions[recipe_name]:
                del self.recipe_subscriptions[recipe_name]

    async def broadcast_recipe_step(self, recipe_name: str, step_data: dict[str, Any]) -> None:
        """Broadcast a recipe step update to subscribers."""
        message = {
            "type": "recipe_step",
            "recipe": recipe_name,
            "data": step_data,
        }
        subscribers = self.recipe_subscriptions.get(recipe_name, set())
        await self._send_to_many(subscribers, message)

    async def _send_to_many(self, websockets: set[WebSocket], message: dict) -> None:
        """Send a message to multiple WebSocket connections."""
        disconnected = []
        for websocket in websockets:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(websocket)

        # Clean up disconnected sockets
        for ws in disconnected:
            await self.disconnect(ws)

    async def send_personal(self, websocket: WebSocket, message: dict) -> None:
        """Send a message to a specific WebSocket."""
        try:
            await websocket.send_json(message)
        except Exception:
            await self.disconnect(websocket)

    def _has_status_subscription(self, websocket: WebSocket) -> bool:
        if websocket in self.global_status_subscriptions:
            return True
        return any(websocket in subscribers for subscribers in self.status_subscriptions.values())

    def _ensure_status_poller(self, websocket: WebSocket) -> None:
        if websocket in self.status_pollers:
            return
        self.status_pollers[websocket] = asyncio.create_task(self._status_poll_loop(websocket))

    async def _status_poll_loop(self, websocket: WebSocket) -> None:
        while websocket in self.active_connections:
            if not self._has_status_subscription(websocket):
                break
            try:
                await self._send_status_snapshot(websocket)
            except Exception:
                await self.disconnect(websocket)
                break
            await asyncio.sleep(STATUS_POLL_INTERVAL)

    async def _send_status_snapshot(self, websocket: WebSocket) -> None:
        init_database()
        if websocket in self.global_status_subscriptions:
            processes = Process.query().all()
        else:
            process_ids = [
                process_id for process_id, subscribers in self.status_subscriptions.items() if websocket in subscribers
            ]
            processes = [Process.from_id(process_id) for process_id in process_ids]
        for process in processes:
            if not process:
                continue
            await self.send_personal(
                websocket,
                {
                    "type": "status",
                    "process_id": process._id,
                    "data": _build_status_payload(process),
                },
            )


# Global connection manager instance
manager = ConnectionManager()


def get_connection_manager() -> ConnectionManager:
    """Get the global ConnectionManager instance."""
    return manager


# Event handlers that bridge ProcessManager events to WebSocket broadcasts
async def _handle_status_change(data: dict[str, Any]) -> None:
    """Handle status change events from ProcessManager."""
    process_id = data.get("process_id")
    if process_id is not None:
        init_database()
        process = Process.from_id(process_id)
        if process:
            data = {**data, **_build_status_payload(process)}
        await manager.broadcast_status(process_id, data)


async def _handle_log_entry(data: dict[str, Any]) -> None:
    """Handle log entry events from ProcessManager."""
    process_id = data.get("process_id")
    if process_id is not None:
        await manager.broadcast_log(process_id, data)


async def _handle_recipe_step(data: dict[str, Any]) -> None:
    """Handle recipe step events from RecipeExecutor."""
    recipe_name = data.get("recipe")
    if recipe_name is not None:
        await manager.broadcast_recipe_step(recipe_name, data)


def setup_event_handlers() -> None:
    """Setup event handlers to bridge ProcessManager events to WebSocket."""
    event_bus = get_event_bus()
    event_bus.subscribe(EVENT_STATUS_CHANGE, _handle_status_change)
    event_bus.subscribe(EVENT_LOG_ENTRY, _handle_log_entry)
    event_bus.subscribe(EVENT_RECIPE_STEP, _handle_recipe_step)


# Setup event handlers when module loads
setup_event_handlers()


def _build_status_payload(process: Process) -> dict[str, Any]:
    data: dict[str, Any] = {
        "status": process.status,
        "pid": process.pid,
    }
    if process.pid and process.status == "running":
        linux_state = get_linux_process_state(process.pid)
        if linux_state:
            data["linux_state"] = linux_state
            if linux_state["state_code"] == "D":
                data["warning"] = "Process in uninterruptible sleep (D state) - may be stuck on I/O"
            elif linux_state["state_code"] == "Z":
                data["warning"] = "Process is a zombie - parent has not reaped it"
            elif linux_state["state_code"] == "T":
                data["warning"] = "Process is stopped (possibly by debugger or signal)"
    return data


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates.

    Protocol:
    Client -> Server:
        {"action": "subscribe_logs", "process_id": 1}
        {"action": "unsubscribe_logs", "process_id": 1}
        {"action": "subscribe_status", "process_id": 1}  # specific process
        {"action": "subscribe_status"}  # all processes
        {"action": "unsubscribe_status", "process_id": 1}
        {"action": "unsubscribe_status"}  # all processes
        {"action": "ping"}

    Server -> Client:
        {"type": "log", "process_id": 1, "data": {"timestamp": "...", "stream": "stdout", "line": "..."}}
        {"type": "status", "process_id": 1, "data": {"status": "running", "pid": 12345, "linux_state": {...}}}
        {"type": "subscribed", "action": "subscribe_logs", "process_id": 1}
        {"type": "unsubscribed", "action": "unsubscribe_logs", "process_id": 1}
        {"type": "pong"}
        {"type": "error", "message": "..."}
    """
    await manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                await manager.send_personal(
                    websocket,
                    {"type": "error", "message": "Invalid JSON"},
                )
                continue

            action = message.get("action")
            process_id = message.get("process_id")

            if action == "ping":
                await manager.send_personal(websocket, {"type": "pong"})

            elif action == "subscribe_logs":
                if process_id is None:
                    await manager.send_personal(
                        websocket,
                        {"type": "error", "message": "process_id required for subscribe_logs"},
                    )
                else:
                    await manager.subscribe_logs(websocket, process_id)
                    await manager.send_personal(
                        websocket,
                        {
                            "type": "subscribed",
                            "action": "subscribe_logs",
                            "process_id": process_id,
                        },
                    )

            elif action == "unsubscribe_logs":
                if process_id is None:
                    await manager.send_personal(
                        websocket,
                        {"type": "error", "message": "process_id required for unsubscribe_logs"},
                    )
                else:
                    await manager.unsubscribe_logs(websocket, process_id)
                    await manager.send_personal(
                        websocket,
                        {
                            "type": "unsubscribed",
                            "action": "unsubscribe_logs",
                            "process_id": process_id,
                        },
                    )

            elif action == "subscribe_status":
                manager.subscribe_status(websocket, process_id)
                response = {"type": "subscribed", "action": "subscribe_status"}
                if process_id is not None:
                    response["process_id"] = process_id
                await manager.send_personal(websocket, response)

            elif action == "unsubscribe_status":
                manager.unsubscribe_status(websocket, process_id)
                response = {"type": "unsubscribed", "action": "unsubscribe_status"}
                if process_id is not None:
                    response["process_id"] = process_id
                await manager.send_personal(websocket, response)

            elif action == "subscribe_recipe":
                recipe_name = message.get("recipe")
                if recipe_name is None:
                    await manager.send_personal(
                        websocket,
                        {"type": "error", "message": "recipe required for subscribe_recipe"},
                    )
                else:
                    manager.subscribe_recipe(websocket, recipe_name)
                    await manager.send_personal(
                        websocket,
                        {
                            "type": "subscribed",
                            "action": "subscribe_recipe",
                            "recipe": recipe_name,
                        },
                    )

            elif action == "unsubscribe_recipe":
                recipe_name = message.get("recipe")
                if recipe_name is None:
                    await manager.send_personal(
                        websocket,
                        {"type": "error", "message": "recipe required for unsubscribe_recipe"},
                    )
                else:
                    manager.unsubscribe_recipe(websocket, recipe_name)
                    await manager.send_personal(
                        websocket,
                        {
                            "type": "unsubscribed",
                            "action": "unsubscribe_recipe",
                            "recipe": recipe_name,
                        },
                    )

            else:
                await manager.send_personal(
                    websocket,
                    {"type": "error", "message": f"Unknown action: {action}"},
                )

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
