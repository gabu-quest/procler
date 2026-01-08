"""Tests for WebSocket functionality (Phase 7)."""

import pytest
from fastapi.testclient import TestClient

from procgler.api import create_app
from procgler.api.routes.ws import ConnectionManager, get_connection_manager
from procgler.core.events import EVENT_LOG_ENTRY, EVENT_STATUS_CHANGE, get_event_bus


@pytest.fixture
def client():
    """Create a test client for the API."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def ws_manager():
    """Get a fresh ConnectionManager for testing."""
    return ConnectionManager()


class TestConnectionManager:
    """Tests for ConnectionManager class."""

    def test_connect_disconnect(self, ws_manager):
        """Test connecting and disconnecting."""
        # Create mock websocket
        class MockWebSocket:
            async def accept(self):
                pass

            async def send_json(self, data):
                pass

        ws = MockWebSocket()

        # Simulate connect
        import asyncio

        asyncio.run(ws_manager.connect(ws))
        assert ws in ws_manager.active_connections

        # Simulate disconnect
        ws_manager.disconnect(ws)
        assert ws not in ws_manager.active_connections

    def test_subscribe_logs(self, ws_manager):
        """Test log subscription."""

        class MockWebSocket:
            pass

        ws = MockWebSocket()
        ws_manager.active_connections.append(ws)

        # Subscribe
        ws_manager.subscribe_logs(ws, process_id=1)
        assert 1 in ws_manager.log_subscriptions
        assert ws in ws_manager.log_subscriptions[1]

        # Unsubscribe
        ws_manager.unsubscribe_logs(ws, process_id=1)
        assert 1 not in ws_manager.log_subscriptions or ws not in ws_manager.log_subscriptions.get(
            1, set()
        )

    def test_subscribe_status(self, ws_manager):
        """Test status subscription."""

        class MockWebSocket:
            pass

        ws = MockWebSocket()
        ws_manager.active_connections.append(ws)

        # Subscribe to specific process
        ws_manager.subscribe_status(ws, process_id=1)
        assert 1 in ws_manager.status_subscriptions
        assert ws in ws_manager.status_subscriptions[1]

        # Subscribe to all processes
        ws_manager.subscribe_status(ws, process_id=None)
        assert ws in ws_manager.global_status_subscriptions

        # Unsubscribe
        ws_manager.unsubscribe_status(ws, process_id=1)
        ws_manager.unsubscribe_status(ws, process_id=None)
        assert ws not in ws_manager.global_status_subscriptions

    async def test_broadcast_log(self, ws_manager):
        """Test broadcasting log entries."""
        received = []

        class MockWebSocket:
            async def send_json(self, data):
                received.append(data)

        ws = MockWebSocket()
        ws_manager.active_connections.append(ws)
        ws_manager.subscribe_logs(ws, process_id=1)

        await ws_manager.broadcast_log(
            process_id=1, log_data={"line": "test log", "stream": "stdout"}
        )

        assert len(received) == 1
        assert received[0]["type"] == "log"
        assert received[0]["process_id"] == 1
        assert received[0]["data"]["line"] == "test log"

    async def test_broadcast_status(self, ws_manager):
        """Test broadcasting status changes."""
        received = []

        class MockWebSocket:
            async def send_json(self, data):
                received.append(data)

        ws = MockWebSocket()
        ws_manager.active_connections.append(ws)
        ws_manager.subscribe_status(ws, process_id=1)

        await ws_manager.broadcast_status(
            process_id=1, status_data={"status": "running", "pid": 12345}
        )

        assert len(received) == 1
        assert received[0]["type"] == "status"
        assert received[0]["process_id"] == 1
        assert received[0]["data"]["status"] == "running"

    async def test_global_status_subscription(self, ws_manager):
        """Test that global subscribers receive all status updates."""
        received = []

        class MockWebSocket:
            async def send_json(self, data):
                received.append(data)

        ws = MockWebSocket()
        ws_manager.active_connections.append(ws)
        ws_manager.subscribe_status(ws, process_id=None)  # Global subscription

        # Broadcast for different processes
        await ws_manager.broadcast_status(process_id=1, status_data={"status": "running"})
        await ws_manager.broadcast_status(process_id=2, status_data={"status": "stopped"})

        assert len(received) == 2
        assert received[0]["process_id"] == 1
        assert received[1]["process_id"] == 2

    def test_disconnect_cleans_subscriptions(self, ws_manager):
        """Test that disconnect removes all subscriptions."""

        class MockWebSocket:
            pass

        ws = MockWebSocket()
        ws_manager.active_connections.append(ws)
        ws_manager.subscribe_logs(ws, process_id=1)
        ws_manager.subscribe_logs(ws, process_id=2)
        ws_manager.subscribe_status(ws, process_id=1)
        ws_manager.subscribe_status(ws, process_id=None)

        ws_manager.disconnect(ws)

        assert ws not in ws_manager.active_connections
        assert ws not in ws_manager.global_status_subscriptions
        assert 1 not in ws_manager.log_subscriptions or ws not in ws_manager.log_subscriptions.get(
            1, set()
        )


class TestWebSocketEndpoint:
    """Tests for WebSocket endpoint."""

    def test_websocket_connect(self, client):
        """Test connecting to WebSocket."""
        with client.websocket_connect("/api/ws") as websocket:
            # Send ping
            websocket.send_json({"action": "ping"})
            response = websocket.receive_json()
            assert response["type"] == "pong"

    def test_websocket_subscribe_logs(self, client):
        """Test subscribing to logs via WebSocket."""
        with client.websocket_connect("/api/ws") as websocket:
            websocket.send_json({"action": "subscribe_logs", "process_id": 1})
            response = websocket.receive_json()
            assert response["type"] == "subscribed"
            assert response["action"] == "subscribe_logs"
            assert response["process_id"] == 1

    def test_websocket_subscribe_logs_missing_process_id(self, client):
        """Test subscribing to logs without process_id."""
        with client.websocket_connect("/api/ws") as websocket:
            websocket.send_json({"action": "subscribe_logs"})
            response = websocket.receive_json()
            assert response["type"] == "error"
            assert "process_id required" in response["message"]

    def test_websocket_unsubscribe_logs(self, client):
        """Test unsubscribing from logs via WebSocket."""
        with client.websocket_connect("/api/ws") as websocket:
            # Subscribe first
            websocket.send_json({"action": "subscribe_logs", "process_id": 1})
            websocket.receive_json()

            # Unsubscribe
            websocket.send_json({"action": "unsubscribe_logs", "process_id": 1})
            response = websocket.receive_json()
            assert response["type"] == "unsubscribed"
            assert response["action"] == "unsubscribe_logs"

    def test_websocket_subscribe_status(self, client):
        """Test subscribing to status updates via WebSocket."""
        with client.websocket_connect("/api/ws") as websocket:
            # Subscribe to specific process
            websocket.send_json({"action": "subscribe_status", "process_id": 1})
            response = websocket.receive_json()
            assert response["type"] == "subscribed"
            assert response["action"] == "subscribe_status"
            assert response["process_id"] == 1

            # Subscribe to all processes
            websocket.send_json({"action": "subscribe_status"})
            response = websocket.receive_json()
            assert response["type"] == "subscribed"
            assert response["action"] == "subscribe_status"
            assert "process_id" not in response

    def test_websocket_unknown_action(self, client):
        """Test sending unknown action."""
        with client.websocket_connect("/api/ws") as websocket:
            websocket.send_json({"action": "unknown_action"})
            response = websocket.receive_json()
            assert response["type"] == "error"
            assert "Unknown action" in response["message"]

    def test_websocket_invalid_json(self, client):
        """Test sending invalid JSON."""
        with client.websocket_connect("/api/ws") as websocket:
            websocket.send_text("not valid json")
            response = websocket.receive_json()
            assert response["type"] == "error"
            assert "Invalid JSON" in response["message"]


class TestEventBus:
    """Tests for EventBus functionality."""

    async def test_event_bus_subscribe_emit(self):
        """Test basic subscribe and emit."""
        received = []

        async def handler(data):
            received.append(data)

        bus = get_event_bus()
        bus.subscribe("test_event", handler)
        await bus.emit("test_event", {"key": "value"})

        assert len(received) == 1
        assert received[0]["key"] == "value"

    async def test_event_bus_unsubscribe(self):
        """Test unsubscribe."""
        received = []

        async def handler(data):
            received.append(data)

        bus = get_event_bus()
        bus.subscribe("test_event", handler)
        bus.unsubscribe("test_event", handler)
        await bus.emit("test_event", {"key": "value"})

        assert len(received) == 0

    async def test_event_bus_multiple_handlers(self):
        """Test multiple handlers for same event."""
        received1 = []
        received2 = []

        async def handler1(data):
            received1.append(data)

        async def handler2(data):
            received2.append(data)

        bus = get_event_bus()
        bus.subscribe("test_event", handler1)
        bus.subscribe("test_event", handler2)
        await bus.emit("test_event", {"key": "value"})

        assert len(received1) == 1
        assert len(received2) == 1
