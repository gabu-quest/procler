"""Process group management."""

from __future__ import annotations

import asyncio
from typing import Any

from ..config import DependencyCondition, get_config
from .health import get_health_checker
from .process_manager import get_process_manager


class GroupManager:
    """Manages process groups with ordered operations and dependency support."""

    def __init__(self):
        self._process_manager = get_process_manager()
        self._health_checker = get_health_checker()

    def list_groups(self) -> dict[str, Any]:
        """List all defined groups."""
        config = get_config()

        groups_data = []
        for name, group in config.groups.items():
            groups_data.append(
                {
                    "name": name,
                    "description": group.description,
                    "processes": group.processes,
                    "stop_order": group.get_stop_order(),
                }
            )

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

    async def start_group(
        self,
        name: str,
        respect_dependencies: bool = True,
        dependency_timeout: float = 60.0,
    ) -> dict[str, Any]:
        """
        Start all processes in a group in order.

        Args:
            name: Group name
            respect_dependencies: If True, wait for process dependencies before starting
            dependency_timeout: Max seconds to wait for each dependency
        """
        config = get_config()

        if name not in config.groups:
            return {
                "success": False,
                "error": f"Group '{name}' not found",
                "error_code": "group_not_found",
                "suggestion": "Run 'procler group list' to see available groups",
            }

        group = config.groups[name]
        results = []
        all_success = True

        for proc_name in group.processes:
            # Check if process is defined in config
            if proc_name not in config.processes:
                results.append(
                    {
                        "process": proc_name,
                        "success": False,
                        "error": f"Process '{proc_name}' not defined in config",
                        "error_code": "process_not_in_config",
                        "suggestion": "Add process definition to .procler/config.yaml",
                    }
                )
                all_success = False
                continue

            proc_def = config.processes[proc_name]

            # Check dependencies before starting (applies to all replicas)
            if respect_dependencies and proc_def.depends_on:
                dep_result = await self._wait_for_dependencies(proc_name, proc_def, config, dependency_timeout)
                if not dep_result["success"]:
                    results.append(
                        {
                            "process": proc_name,
                            "success": False,
                            "error": dep_result["error"],
                            "dependency_failures": dep_result.get("failures", []),
                        }
                    )
                    all_success = False
                    continue

            # Expand replicas: if replicas > 1, start each instance
            replica_names = config.get_replica_names(proc_name)

            for instance_name in replica_names:
                # Ensure process exists in runtime DB
                await self._ensure_process_in_db(instance_name, proc_def)

                # Register ready_log_line pattern before starting (so log callback can match)
                if proc_def.ready_log_line:
                    from sqler.query import SQLerField as F

                    from ..models import Process

                    proc_results = Process.query().filter(F("name") == instance_name).all()
                    if proc_results:
                        self._process_manager.register_ready_pattern(proc_results[0]._id, proc_def.ready_log_line)

                # Inject PROCLER_REPLICA_INDEX for replicas
                if proc_def.replicas > 1:
                    # Extract index from name (e.g., "worker-2" -> 2)
                    replica_index = instance_name.rsplit("-", 1)[-1]
                    self._set_replica_env(instance_name, replica_index)

                # Start the process
                result = await self._process_manager.start(instance_name)

                # Start health checking if configured
                if proc_def.healthcheck:
                    self._health_checker.register_process(instance_name, proc_def.healthcheck)
                    asyncio.create_task(self._health_checker.start_checking(instance_name, proc_def.healthcheck))

                results.append(
                    {
                        "process": instance_name,
                        "success": result["success"],
                        "status": result.get("data", {}).get("status"),
                        "error": result.get("error"),
                    }
                )

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

    async def _wait_for_dependencies(
        self,
        proc_name: str,
        proc_def,
        config,
        timeout: float,
    ) -> dict[str, Any]:
        """Wait for all dependencies of a process to be ready."""
        dependencies = proc_def.get_dependencies()
        failures = []

        for dep in dependencies:
            dep_name = dep.name

            # Check if dependency exists
            if dep_name not in config.processes:
                failures.append(
                    {
                        "dependency": dep_name,
                        "error": "Dependency not defined in config",
                    }
                )
                continue

            dep_def = config.processes[dep_name]

            # Check if dependency is running
            status_result = await self._process_manager.status(dep_name)
            if not status_result["success"]:
                failures.append(
                    {
                        "dependency": dep_name,
                        "error": f"Could not get status: {status_result.get('error')}",
                    }
                )
                continue

            proc_status = status_result.get("data", {}).get("process", {}).get("status")

            if proc_status != "running":
                failures.append(
                    {
                        "dependency": dep_name,
                        "error": f"Dependency not running (status: {proc_status})",
                        "condition": dep.condition.value,
                    }
                )
                continue

            # If condition is 'healthy', wait for health check
            if dep.condition == DependencyCondition.HEALTHY:
                if not dep_def.healthcheck:
                    failures.append(
                        {
                            "dependency": dep_name,
                            "error": "Dependency requires healthy condition but has no healthcheck",
                        }
                    )
                    continue

                # Wait for healthy status
                is_healthy = await self._health_checker.wait_for_healthy(dep_name, dep_def.healthcheck, timeout)
                if not is_healthy:
                    failures.append(
                        {
                            "dependency": dep_name,
                            "error": f"Dependency not healthy after {timeout}s",
                            "condition": "healthy",
                        }
                    )
                    continue

            # If condition is 'log_ready', wait for ready_log_line match
            elif dep.condition == DependencyCondition.LOG_READY:
                if not dep_def.ready_log_line:
                    failures.append(
                        {
                            "dependency": dep_name,
                            "error": "Dependency requires log_ready condition but has no ready_log_line",
                        }
                    )
                    continue

                # Wait for log_ready with polling
                is_ready = await self._wait_for_log_ready(dep_name, timeout)
                if not is_ready:
                    failures.append(
                        {
                            "dependency": dep_name,
                            "error": f"Dependency log_ready not matched after {timeout}s",
                            "condition": "log_ready",
                        }
                    )
                    continue

        if failures:
            return {
                "success": False,
                "error": f"Dependencies not satisfied for '{proc_name}'",
                "failures": failures,
            }

        return {"success": True}

    async def stop_group(self, name: str) -> dict[str, Any]:
        """Stop all processes in a group in stop order."""
        config = get_config()

        if name not in config.groups:
            return {
                "success": False,
                "error": f"Group '{name}' not found",
                "error_code": "group_not_found",
                "suggestion": "Run 'procler group list' to see available groups",
            }

        group = config.groups[name]
        stop_order = group.get_stop_order()
        results = []
        all_success = True

        for proc_name in stop_order:
            # Check if process is defined
            if proc_name not in config.processes:
                results.append(
                    {
                        "process": proc_name,
                        "success": False,
                        "error": f"Process '{proc_name}' not defined in config",
                        "error_code": "process_not_in_config",
                        "suggestion": "Add process definition to .procler/config.yaml",
                    }
                )
                all_success = False
                continue

            proc_def = config.processes[proc_name]
            replica_names = config.get_replica_names(proc_name)

            for instance_name in replica_names:
                # Stop health checking first
                await self._health_checker.stop_checking(instance_name)

                # Ensure process exists in runtime DB
                await self._ensure_process_in_db(instance_name, proc_def)

                # Stop the process
                result = await self._process_manager.stop(instance_name)
                results.append(
                    {
                        "process": instance_name,
                        "success": result["success"],
                        "status": result.get("data", {}).get("status"),
                        "error": result.get("error"),
                    }
                )

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
        """Get status of all processes in a group, including health information."""
        config = get_config()

        if name not in config.groups:
            return {
                "success": False,
                "error": f"Group '{name}' not found",
                "error_code": "group_not_found",
                "suggestion": "Run 'procler group list' to see available groups",
            }

        group = config.groups[name]
        statuses = []

        for proc_name in group.processes:
            if proc_name not in config.processes:
                statuses.append(
                    {
                        "process": proc_name,
                        "status": "not_defined",
                        "error": "Not defined in config",
                    }
                )
                continue

            proc_def = config.processes[proc_name]

            # Ensure process exists in runtime DB
            await self._ensure_process_in_db(proc_name, proc_def)

            result = await self._process_manager.status(proc_name)
            if result["success"]:
                proc_data = result["data"]["process"]
                status_entry = {
                    "process": proc_name,
                    "status": proc_data.get("status", "unknown"),
                    "pid": proc_data.get("pid"),
                    "uptime_seconds": proc_data.get("uptime_seconds"),
                    "linux_state": proc_data.get("linux_state"),
                }

                # Include health status if process has health check
                if proc_def.healthcheck:
                    status_entry["health"] = self._health_checker.to_dict(proc_name)

                # Include dependency info
                if proc_def.depends_on:
                    status_entry["depends_on"] = [
                        {"name": d.name, "condition": d.condition.value} for d in proc_def.get_dependencies()
                    ]

                statuses.append(status_entry)
            else:
                statuses.append(
                    {
                        "process": proc_name,
                        "status": "unknown",
                        "error": result.get("error"),
                    }
                )

        return {
            "success": True,
            "data": {
                "group": name,
                "description": group.description,
                "statuses": statuses,
            },
        }

    def _set_replica_env(self, instance_name: str, replica_index: str) -> None:
        """Set PROCLER_REPLICA_INDEX env var on a process in the DB."""
        from sqler.query import SQLerField as F

        from ..models import Process

        results = Process.query().filter(F("name") == instance_name).all()
        if results:
            proc = results[0]
            env = proc.env or {}
            env["PROCLER_REPLICA_INDEX"] = replica_index
            proc.env = env
            proc.save()

    async def _wait_for_log_ready(self, process_name: str, timeout: float) -> bool:
        """Wait for a process to emit its ready_log_line pattern."""
        from datetime import datetime

        from sqler.query import SQLerField as F

        from ..models import Process

        # Find the process to get its ID
        results = Process.query().filter(F("name") == process_name).all()
        if not results:
            return False

        process_id = results[0]._id
        start = datetime.now()

        while True:
            elapsed = (datetime.now() - start).total_seconds()
            if elapsed >= timeout:
                return False

            if self._process_manager.is_process_ready(process_id):
                return True

            # Check if process is still running
            status_result = await self._process_manager.status(process_name)
            if status_result.get("success"):
                proc_status = status_result.get("data", {}).get("process", {}).get("status")
                if proc_status not in ("running", "starting"):
                    return False

            await asyncio.sleep(0.2)

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
        namespace = getattr(proc_def, "namespace", "default")
        process = Process(
            name=name,
            command=proc_def.command,
            context_type=proc_def.context.value,
            container_name=proc_def.container,
            cwd=proc_def.cwd,
            tags=tags,
            namespace=namespace,
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
