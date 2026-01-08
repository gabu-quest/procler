"""CLI interface for Procgler."""

import json
import sys
from datetime import datetime
from typing import Any

import click

from . import __version__

# JSON output utilities


def output_json(data: dict[str, Any]) -> None:
    """Output JSON to stdout."""
    click.echo(json.dumps(data, indent=2, default=str))


def success_response(data: dict[str, Any] | None = None) -> dict[str, Any]:
    """Create a success response envelope."""
    response = {"success": True}
    if data is not None:
        response["data"] = data
    return response


def error_response(
    error: str,
    error_code: str | None = None,
    suggestion: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    """Create an error response envelope."""
    response = {"success": False, "error": error}
    if error_code:
        response["error_code"] = error_code
    if suggestion:
        response["suggestion"] = suggestion
    response.update(extra)
    return response


# CLI schema for capabilities command

CLI_SCHEMA = {
    "name": "procgler",
    "version": __version__,
    "description": "LLM-first process manager for developers",
    "commands": {
        "capabilities": {
            "description": "Returns JSON schema of all commands",
            "arguments": [],
            "options": [],
        },
        "status": {
            "description": "Show status of all processes or a specific one",
            "arguments": [
                {
                    "name": "name",
                    "required": False,
                    "description": "Process name (optional, shows all if omitted)",
                }
            ],
            "options": [],
        },
        "start": {
            "description": "Start a process (idempotent - no-op if running)",
            "arguments": [
                {"name": "name", "required": True, "description": "Process name"}
            ],
            "options": [],
        },
        "stop": {
            "description": "Stop a process (idempotent - no-op if stopped)",
            "arguments": [
                {"name": "name", "required": True, "description": "Process name"}
            ],
            "options": [],
        },
        "restart": {
            "description": "Restart a process (stop then start)",
            "arguments": [
                {"name": "name", "required": True, "description": "Process name"}
            ],
            "options": [],
        },
        "define": {
            "description": "Define a new process",
            "arguments": [],
            "options": [
                {"name": "--name", "required": True, "description": "Process name (CLI identifier)"},
                {"name": "--command", "required": True, "description": "Command to execute"},
                {
                    "name": "--context",
                    "required": False,
                    "default": "local",
                    "choices": ["local", "docker"],
                    "description": "Execution context",
                },
                {
                    "name": "--container",
                    "required": False,
                    "description": "Docker container name (required if context=docker)",
                },
                {"name": "--cwd", "required": False, "description": "Working directory"},
                {"name": "--display-name", "required": False, "description": "Human-friendly name"},
                {"name": "--tags", "required": False, "description": "Comma-separated tags"},
            ],
        },
        "remove": {
            "description": "Remove a process definition",
            "arguments": [
                {"name": "name", "required": True, "description": "Process name"}
            ],
            "options": [],
        },
        "list": {
            "description": "List all process definitions",
            "arguments": [],
            "options": [],
        },
        "logs": {
            "description": "Get logs for a process",
            "arguments": [
                {"name": "name", "required": True, "description": "Process name"}
            ],
            "options": [
                {
                    "name": "--tail",
                    "required": False,
                    "default": 100,
                    "description": "Number of lines to return",
                },
                {
                    "name": "--since",
                    "required": False,
                    "description": "Time filter (e.g., '5m', '1h', ISO timestamp)",
                },
            ],
        },
        "exec": {
            "description": "Execute an arbitrary command",
            "arguments": [
                {"name": "command", "required": True, "description": "Command to execute"}
            ],
            "options": [
                {
                    "name": "--context",
                    "required": False,
                    "default": "local",
                    "choices": ["local", "docker"],
                    "description": "Execution context",
                },
                {
                    "name": "--container",
                    "required": False,
                    "description": "Docker container name",
                },
                {"name": "--cwd", "required": False, "description": "Working directory"},
            ],
        },
        "snippet": {
            "description": "Manage command snippets",
            "subcommands": {
                "list": {
                    "description": "List all snippets",
                    "options": [
                        {"name": "--tag", "required": False, "description": "Filter by tag"}
                    ],
                },
                "save": {
                    "description": "Save a new snippet",
                    "options": [
                        {"name": "--name", "required": True, "description": "Snippet name"},
                        {"name": "--command", "required": True, "description": "Command to save"},
                        {"name": "--description", "required": False, "description": "Description"},
                        {
                            "name": "--context",
                            "required": False,
                            "default": "local",
                            "description": "Execution context",
                        },
                        {"name": "--container", "required": False, "description": "Docker container"},
                        {"name": "--tags", "required": False, "description": "Comma-separated tags"},
                    ],
                },
                "run": {
                    "description": "Run a saved snippet",
                    "arguments": [
                        {"name": "name", "required": True, "description": "Snippet name"}
                    ],
                },
                "remove": {
                    "description": "Remove a snippet",
                    "arguments": [
                        {"name": "name", "required": True, "description": "Snippet name"}
                    ],
                },
            },
        },
        "serve": {
            "description": "Start the web server",
            "arguments": [],
            "options": [
                {"name": "--host", "required": False, "default": "127.0.0.1", "description": "Host to bind"},
                {"name": "--port", "required": False, "default": 8000, "description": "Port to bind"},
                {"name": "--reload", "required": False, "is_flag": True, "description": "Enable hot reload"},
            ],
        },
    },
}


def _get_process_by_name(name: str):
    """Get a process by name using sqler query."""
    from sqler.query import SQLerField as F

    from .db import init_database
    from .models import Process

    init_database()
    results = Process.query().filter(F("name") == name).all()
    return results[0] if results else None


def _process_to_dict(process) -> dict[str, Any]:
    """Convert a Process model to a dict for JSON output."""
    return {
        "id": process._id,
        "name": process.name,
        "display_name": process.display_name,
        "command": process.command,
        "context_type": process.context_type,
        "status": process.status,
        "pid": process.pid,
        "uptime_seconds": process.uptime_seconds,
    }


@click.group()
@click.version_option(version=__version__, prog_name="procgler")
def cli() -> None:
    """Procgler - LLM-first process manager for developers.

    All commands output JSON for easy parsing by scripts and LLMs.
    """
    pass


@cli.command()
def capabilities() -> None:
    """Returns JSON schema of all commands."""
    output_json(success_response(CLI_SCHEMA))


@cli.command()
@click.argument("name", required=False)
def status(name: str | None) -> None:
    """Show status of all processes or a specific one."""
    import asyncio

    from .core import get_process_manager

    manager = get_process_manager()
    result = asyncio.run(manager.status(name))

    output_json(result)
    if not result["success"]:
        sys.exit(1)


@cli.command("list")
def list_processes() -> None:
    """List all process definitions."""
    from .db import init_database
    from .models import Process

    init_database()
    processes = Process.query().all()

    process_data = []
    for process in processes:
        process_data.append(
            {
                "id": process._id,
                "name": process.name,
                "display_name": process.display_name,
                "command": process.command,
                "context_type": process.context_type,
                "container_name": process.container_name,
                "cwd": process.cwd,
                "tags": process.tags or [],
            }
        )

    output_json(success_response({"processes": process_data}))


@cli.command()
@click.option("--name", required=True, help="Process name (CLI identifier)")
@click.option("--command", "cmd", required=True, help="Command to execute")
@click.option(
    "--context",
    type=click.Choice(["local", "docker"]),
    default="local",
    help="Execution context",
)
@click.option("--container", help="Docker container name (required if context=docker)")
@click.option("--cwd", help="Working directory")
@click.option("--display-name", help="Human-friendly name")
@click.option("--tags", help="Comma-separated tags")
def define(
    name: str,
    cmd: str,
    context: str,
    container: str | None,
    cwd: str | None,
    display_name: str | None,
    tags: str | None,
) -> None:
    """Define a new process."""
    from .db import init_database
    from .models import Process

    if context == "docker" and not container:
        output_json(
            error_response(
                "Container name required for docker context",
                error_code="missing_container",
                suggestion="Use --container <name> to specify the Docker container",
            )
        )
        sys.exit(1)

    init_database()

    # Check if process already exists
    existing = _get_process_by_name(name)
    if existing:
        output_json(
            error_response(
                f"Process '{name}' already exists",
                error_code="process_exists",
                suggestion=f"Use 'procgler remove {name}' first, or choose a different name",
            )
        )
        sys.exit(1)

    tag_list = [t.strip() for t in tags.split(",")] if tags else None

    process = Process(
        name=name,
        command=cmd,
        context_type=context,
        display_name=display_name,
        container_name=container,
        cwd=cwd,
        tags=tag_list,
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
    )
    process.save()

    output_json(
        success_response(
            {
                "action": "created",
                "process": {
                    "id": process._id,
                    "name": process.name,
                    "command": process.command,
                    "context_type": process.context_type,
                },
            }
        )
    )


@cli.command()
@click.argument("name")
def remove(name: str) -> None:
    """Remove a process definition."""
    from .db import init_database

    init_database()

    process = _get_process_by_name(name)
    if not process:
        output_json(
            error_response(
                f"Process '{name}' not found",
                error_code="process_not_found",
                suggestion="Run 'procgler list' to see available processes",
            )
        )
        sys.exit(1)

    process.delete()
    output_json(success_response({"action": "removed", "name": name}))


@cli.command()
@click.argument("name")
def start(name: str) -> None:
    """Start a process (idempotent - no-op if running)."""
    import asyncio

    from .core import get_process_manager

    manager = get_process_manager()
    result = asyncio.run(manager.start(name))

    output_json(result)
    if not result["success"]:
        sys.exit(1)


@cli.command()
@click.argument("name")
def stop(name: str) -> None:
    """Stop a process (idempotent - no-op if stopped)."""
    import asyncio

    from .core import get_process_manager

    manager = get_process_manager()
    result = asyncio.run(manager.stop(name))

    output_json(result)
    if not result["success"]:
        sys.exit(1)


@cli.command()
@click.argument("name")
def restart(name: str) -> None:
    """Restart a process (stop then start)."""
    import asyncio

    from .core import get_process_manager

    manager = get_process_manager()
    result = asyncio.run(manager.restart(name))

    output_json(result)
    if not result["success"]:
        sys.exit(1)


@cli.command()
@click.argument("name")
@click.option("--tail", default=100, help="Number of lines to return")
@click.option("--since", help="Time filter (e.g., '5m', '1h', ISO timestamp)")
def logs(name: str, tail: int, since: str | None) -> None:
    """Get logs for a process."""
    import asyncio

    from .core import get_process_manager

    manager = get_process_manager()
    result = asyncio.run(manager.logs(name, tail=tail, since=since))

    output_json(result)
    if not result["success"]:
        sys.exit(1)


@cli.command("exec")
@click.argument("command")
@click.option(
    "--context",
    type=click.Choice(["local", "docker"]),
    default="local",
    help="Execution context",
)
@click.option("--container", help="Docker container name")
@click.option("--cwd", help="Working directory")
@click.option("--timeout", default=60.0, help="Maximum execution time in seconds")
def exec_cmd(
    command: str,
    context: str,
    container: str | None,
    cwd: str | None,
    timeout: float,
) -> None:
    """Execute an arbitrary command."""
    import asyncio

    from .core import get_process_manager

    if context == "docker" and not container:
        output_json(
            error_response(
                "Container name required for docker context",
                error_code="missing_container",
                suggestion="Use --container <name> to specify the Docker container",
            )
        )
        sys.exit(1)

    manager = get_process_manager()
    result = asyncio.run(
        manager.exec_command(
            command=command,
            context_type=context,
            container_name=container,
            cwd=cwd,
            timeout=timeout,
        )
    )

    output_json(result)
    if not result["success"]:
        sys.exit(1)


if __name__ == "__main__":
    cli()
