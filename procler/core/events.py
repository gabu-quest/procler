"""Event system for broadcasting status and log updates."""

import asyncio
from typing import Any, Callable, Coroutine

# Type for async event handlers
EventHandler = Callable[[dict[str, Any]], Coroutine[Any, Any, None]]


class EventBus:
    """Simple event bus for broadcasting events to subscribers."""

    def __init__(self):
        self._handlers: dict[str, list[EventHandler]] = {}

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribe to an event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Unsubscribe from an event type."""
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
            except ValueError:
                pass

    async def emit(self, event_type: str, data: dict[str, Any]) -> None:
        """Emit an event to all subscribers."""
        handlers = self._handlers.get(event_type, [])
        for handler in handlers:
            try:
                await handler(data)
            except Exception:
                pass  # Don't let one handler break others

    def emit_sync(self, event_type: str, data: dict[str, Any]) -> None:
        """Emit an event synchronously (creates task if in async context)."""
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.emit(event_type, data))
        except RuntimeError:
            # No running event loop, skip
            pass


# Event types
EVENT_STATUS_CHANGE = "status_change"
EVENT_LOG_ENTRY = "log_entry"

# Global event bus
_event_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """Get the global EventBus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


def reset_event_bus() -> None:
    """Reset the global EventBus (for testing)."""
    global _event_bus
    _event_bus = None
