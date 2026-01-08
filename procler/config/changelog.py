"""Append-only changelog for tracking config changes."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from .loader import get_changelog_path


class ChangelogAction(str, Enum):
    """Types of changelog actions."""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    EXECUTE = "EXECUTE"  # For recipe executions
    START = "START"  # Process started
    STOP = "STOP"  # Process stopped


def append_changelog(
    action: ChangelogAction,
    entity_type: str,
    entity_name: str,
    details: dict[str, Any] | None = None,
    changelog_path: Path | None = None,
) -> None:
    """
    Append an entry to the changelog.

    Format: [ISO8601] ACTION type:name {json_details}

    Args:
        action: The action performed (CREATE, UPDATE, DELETE, EXECUTE, START, STOP)
        entity_type: Type of entity (process, group, recipe, snippet)
        entity_name: Name of the entity
        details: Optional dict of additional details
        changelog_path: Override path for testing
    """
    try:
        if changelog_path is None:
            changelog_path = get_changelog_path()
    except (ValueError, FileNotFoundError):
        # No config directory found - skip logging silently
        return

    # Ensure directory exists
    changelog_path.parent.mkdir(parents=True, exist_ok=True)

    # Create header if file doesn't exist
    if not changelog_path.exists():
        header = (
            "# Procler Changelog - AUTO-GENERATED\n"
            "# DO NOT EDIT MANUALLY\n"
            "# Format: [ISO8601] ACTION type:name {json_details}\n"
            "#\n"
        )
        changelog_path.write_text(header)

    # Build log entry
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    details_json = json.dumps(details or {}, separators=(",", ":"))
    entry = f"[{timestamp}] {action.value} {entity_type}:{entity_name} {details_json}\n"

    # Append to file
    with open(changelog_path, "a") as f:
        f.write(entry)


def read_changelog(changelog_path: Path | None = None) -> list[dict[str, Any]]:
    """
    Read and parse the changelog.

    Returns list of entries:
    [
        {
            "timestamp": "2024-01-08T12:00:00Z",
            "action": "CREATE",
            "entity_type": "process",
            "entity_name": "api",
            "details": {...}
        },
        ...
    ]
    """
    if changelog_path is None:
        changelog_path = get_changelog_path()

    if not changelog_path.exists():
        return []

    entries = []
    for line in changelog_path.read_text().splitlines():
        line = line.strip()
        # Skip comments and empty lines
        if not line or line.startswith("#"):
            continue

        try:
            # Parse: [TIMESTAMP] ACTION type:name {json}
            # Find the timestamp
            ts_end = line.index("]")
            timestamp = line[1:ts_end]

            # Find the action
            rest = line[ts_end + 2:]  # Skip "] "
            parts = rest.split(" ", 2)
            if len(parts) < 2:
                continue

            action = parts[0]
            entity = parts[1]
            details_str = parts[2] if len(parts) > 2 else "{}"

            # Parse entity type:name
            entity_type, _, entity_name = entity.partition(":")

            # Parse details JSON
            details = json.loads(details_str)

            entries.append({
                "timestamp": timestamp,
                "action": action,
                "entity_type": entity_type,
                "entity_name": entity_name,
                "details": details,
            })
        except (ValueError, json.JSONDecodeError):
            # Skip malformed lines
            continue

    return entries


def get_entity_history(
    entity_type: str,
    entity_name: str,
    changelog_path: Path | None = None,
) -> list[dict[str, Any]]:
    """Get changelog entries for a specific entity."""
    entries = read_changelog(changelog_path)
    return [
        e for e in entries
        if e["entity_type"] == entity_type and e["entity_name"] == entity_name
    ]
