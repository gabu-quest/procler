"""WebSocket handler for real-time updates."""

import asyncio
import json
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ...core.events import EVENT_LOG_ENTRY, EVENT_STATUS_CHANGE, get_event_bus

router = APIRouter()


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

    async def connect(self, websocket: WebSocket) -> None:
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection and all its subscriptions."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        # Remove from all log subscriptions
        for process_id in list(self.log_subscriptions.keys()):
            self.log_subscriptions[process_id].discard(websocket)
            if not self.log_subscriptions[process_id]:
                del self.log_subscriptions[process_id]

        # Remove from all status subscriptions
        for process_id in list(self.status_subscriptions.keys()):
            self.status_subscriptions[process_id].discard(websocket)
            if not self.status_subscriptions[process_id]:
                del self.status_subscriptions[process_id]

        # Remove from global subscriptions
        self.global_status_subscriptions.discard(websocket)

    def subscribe_logs(self, websocket: WebSocket, process_id: int) -> None:
        """Subscribe to log updates for a specific process."""
        if process_id not in self.log_subscriptions:
            self.log_subscriptions[process_id] = set()
        self.log_subscriptions[process_id].add(websocket)

    def unsubscribe_logs(self, websocket: WebSocket, process_id: int) -> None:
        """Unsubscribe from log updates for a specific process."""
        if process_id in self.log_subscriptions:
            self.log_subscriptions[process_id].discard(websocket)
            if not self.log_subscriptions[process_id]:
                del self.log_subscriptions[process_id]

    def subscribe_status(self, websocket: WebSocket, process_id: int | None = None) -> None:
        """Subscribe to status updates for a specific process or all processes."""
        if process_id is None:
            self.global_status_subscriptions.add(websocket)
        else:
            if process_id not in self.status_subscriptions:
                self.status_subscriptions[process_id] = set()
            self.status_subscriptions[process_id].add(websocket)

    def unsubscribe_status(self, websocket: WebSocket, process_id: int | None = None) -> None:
        """Unsubscribe from status updates."""
        if process_id is None:
            self.global_status_subscriptions.discard(websocket)
        elif process_id in self.status_subscriptions:
            self.status_subscriptions[process_id].discard(websocket)
            if not self.status_subscriptions[process_id]:
                del self.status_subscriptions[process_id]

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
            self.disconnect(ws)

    async def send_personal(self, websocket: WebSocket, message: dict) -> None:
        """Send a message to a specific WebSocket."""
        try:
            await websocket.send_json(message)
        except Exception:
            self.disconnect(websocket)


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
        await manager.broadcast_status(process_id, data)


async def _handle_log_entry(data: dict[str, Any]) -> None:
    """Handle log entry events from ProcessManager."""
    process_id = data.get("process_id")
    if process_id is not None:
        await manager.broadcast_log(process_id, data)


def setup_event_handlers() -> None:
    """Setup event handlers to bridge ProcessManager events to WebSocket."""
    event_bus = get_event_bus()
    event_bus.subscribe(EVENT_STATUS_CHANGE, _handle_status_change)
    event_bus.subscribe(EVENT_LOG_ENTRY, _handle_log_entry)


# Setup event handlers when module loads
setup_event_handlers()


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
        {"type": "status", "process_id": 1, "data": {"status": "running", "pid": 12345}}
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
                    manager.subscribe_logs(websocket, process_id)
                    await manager.send_personal(
                        websocket,
                        {"type": "subscribed", "action": "subscribe_logs", "process_id": process_id},
                    )

            elif action == "unsubscribe_logs":
                if process_id is None:
                    await manager.send_personal(
                        websocket,
                        {"type": "error", "message": "process_id required for unsubscribe_logs"},
                    )
                else:
                    manager.unsubscribe_logs(websocket, process_id)
                    await manager.send_personal(
                        websocket,
                        {"type": "unsubscribed", "action": "unsubscribe_logs", "process_id": process_id},
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

            else:
                await manager.send_personal(
                    websocket,
                    {"type": "error", "message": f"Unknown action: {action}"},
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)
