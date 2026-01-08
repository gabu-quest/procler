"""Process group management."""

from __future__ import annotations

from typing import Any

from ..config import get_config, GroupDef
from . import get_process_manager


class GroupManager:
    """Manages process groups with ordered operations."""

    def __init__(self):
        self._process_manager = get_process_manager()

    def list_groups(self) -> dict[str, Any]:
        """List all defined groups."""
        config = get_config()

        groups_data = []
        for name, group in config.groups.items():
            groups_data.append({
                "name": name,
                "description": group.description,
                "processes": group.processes,
                "stop_order": group.get_stop_order(),
            })

        return {
            "success": True,
            "data": {
                "groups": groups_data,
                "count": len(groups_data),
            },
        }

    def get_group(self, name: str) -> dict[str, Any]:
        """Get a specific group by name."""
        config = get_config()

        if name not in config.groups:
            return {
                "success": False,
                "error": f"Group '{name}' not found",
                "error_code": "group_not_found",
                "suggestion": "Run 'procler group list' to see available groups",
            }

        group = config.groups[name]
        return {
            "success": True,
            "data": {
                "group": {
                    "name": name,
                    "description": group.description,
                    "processes": group.processes,
                    "stop_order": group.get_stop_order(),
                }
            },
        }

    async def start_group(self, name: str) -> dict[str, Any]:
        """Start all processes in a group in order."""
        config = get_config()

        if name not in config.groups:
            return {
                "success": False,
                "error": f"Group '{name}' not found",
                "error_code": "group_not_found",
            }

        group = config.groups[name]
        results = []
        all_success = True

        for proc_name in group.processes:
            # Check if process is defined in config
            if proc_name not in config.processes:
                results.append({
                    "process": proc_name,
                    "success": False,
                    "error": f"Process '{proc_name}' not defined in config",
                })
                all_success = False
                continue

            # Ensure process exists in runtime DB
            await self._ensure_process_in_db(proc_name, config.processes[proc_name])

            # Start the process
            result = await self._process_manager.start(proc_name)
            results.append({
                "process": proc_name,
                "success": result["success"],
                "status": result.get("data", {}).get("status"),
                "error": result.get("error"),
            })

            if not result["success"]:
                all_success = False

        return {
            "success": all_success,
            "data": {
                "group": name,
                "action": "started",
                "results": results,
            },
        }

    async def stop_group(self, name: str) -> dict[str, Any]:
        """Stop all processes in a group in stop order."""
        config = get_config()

        if name not in config.groups:
            return {
                "success": False,
                "error": f"Group '{name}' not found",
                "error_code": "group_not_found",
            }

        group = config.groups[name]
        stop_order = group.get_stop_order()
        results = []
        all_success = True

        for proc_name in stop_order:
            # Check if process is defined
            if proc_name not in config.processes:
                results.append({
                    "process": proc_name,
                    "success": False,
                    "error": f"Process '{proc_name}' not defined in config",
                })
                all_success = False
                continue

            # Ensure process exists in runtime DB
            await self._ensure_process_in_db(proc_name, config.processes[proc_name])

            # Stop the process
            result = await self._process_manager.stop(proc_name)
            results.append({
                "process": proc_name,
                "success": result["success"],
                "status": result.get("data", {}).get("status"),
                "error": result.get("error"),
            })

            if not result["success"]:
                all_success = False

        return {
            "success": all_success,
            "data": {
                "group": name,
                "action": "stopped",
                "results": results,
            },
        }

    async def status_group(self, name: str) -> dict[str, Any]:
        """Get status of all processes in a group."""
        config = get_config()

        if name not in config.groups:
            return {
                "success": False,
                "error": f"Group '{name}' not found",
                "error_code": "group_not_found",
            }

        group = config.groups[name]
        statuses = []

        for proc_name in group.processes:
            if proc_name not in config.processes:
                statuses.append({
                    "process": proc_name,
                    "status": "not_defined",
                    "error": "Not defined in config",
                })
                continue

            # Ensure process exists in runtime DB
            await self._ensure_process_in_db(proc_name, config.processes[proc_name])

            result = await self._process_manager.status(proc_name)
            if result["success"]:
                proc_data = result["data"]["process"]
                statuses.append({
                    "process": proc_name,
                    "status": proc_data.get("status", "unknown"),
                    "pid": proc_data.get("pid"),
                    "uptime_seconds": proc_data.get("uptime_seconds"),
                })
            else:
                statuses.append({
                    "process": proc_name,
                    "status": "unknown",
                    "error": result.get("error"),
                })

        return {
            "success": True,
            "data": {
                "group": name,
                "description": group.description,
                "statuses": statuses,
            },
        }

    async def _ensure_process_in_db(self, name: str, proc_def) -> None:
        """Ensure a process from config exists in the runtime database."""
        from datetime import datetime
        from sqler.query import SQLerField as F
        from ..db import init_database
        from ..models import Process

        init_database()

        # Check if already exists
        existing = Process.query().filter(F("name") == name).all()
        if existing:
            return

        # Create from config definition
        tags = proc_def.tags if proc_def.tags else None
        process = Process(
            name=name,
            command=proc_def.command,
            context_type=proc_def.context.value,
            container_name=proc_def.container,
            cwd=proc_def.cwd,
            tags=tags,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        process.save()


# Singleton
_group_manager: GroupManager | None = None


def get_group_manager() -> GroupManager:
    """Get the singleton GroupManager instance."""
    global _group_manager
    if _group_manager is None:
        _group_manager = GroupManager()
    return _group_manager


def reset_group_manager() -> None:
    """Reset the singleton (for testing)."""
    global _group_manager
    _group_manager = None
