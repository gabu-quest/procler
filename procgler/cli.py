"""CLI interface for Procgler."""

import json
import sys
from typing import Any, Optional

import click

from . import __version__

# JSON output utilities


def output_json(data: dict[str, Any]) -> None:
    """Output JSON to stdout."""
    click.echo(json.dumps(data, indent=2, default=str))


def success_response(data: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Create a success response envelope."""
    response = {"success": True}
    if data is not None:
        response["data"] = data
    return response


def error_response(
    error: str,
    error_code: Optional[str] = None,
    suggestion: Optional[str] = None,
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
def status(name: Optional[str]) -> None:
    """Show status of all processes or a specific one."""
    from .db import get_database
    from .models import ProcessInfo

    db = get_database()

    if name:
        process = db.get_process_by_name(name)
        if not process:
            output_json(
                error_response(
                    f"Process '{name}' not found",
                    error_code="process_not_found",
                    suggestion="Run 'procgler list' to see available processes",
                )
            )
            sys.exit(1)

        state = db.get_process_state(process.id)
        info = ProcessInfo(definition=process, state=state)
        output_json(
            success_response(
                {
                    "process": {
                        "id": info.definition.id,
                        "name": info.name,
                        "display_name": info.definition.display_name,
                        "command": info.definition.command,
                        "context_type": info.definition.context_type.value,
                        "status": info.status.value,
                        "pid": info.pid,
                        "uptime_seconds": info.uptime_seconds,
                    }
                }
            )
        )
    else:
        processes = db.list_processes()
        process_data = []
        for process in processes:
            state = db.get_process_state(process.id)
            info = ProcessInfo(definition=process, state=state)
            process_data.append(
                {
                    "id": info.definition.id,
                    "name": info.name,
                    "display_name": info.definition.display_name,
                    "command": info.definition.command,
                    "context_type": info.definition.context_type.value,
                    "status": info.status.value,
                    "pid": info.pid,
                    "uptime_seconds": info.uptime_seconds,
                }
            )
        output_json(success_response({"processes": process_data}))


@cli.command("list")
def list_processes() -> None:
    """List all process definitions."""
    from .db import get_database

    db = get_database()
    processes = db.list_processes()

    process_data = []
    for process in processes:
        process_data.append(
            {
                "id": process.id,
                "name": process.name,
                "display_name": process.display_name,
                "command": process.command,
                "context_type": process.context_type.value,
                "container_name": process.container_name,
                "cwd": process.cwd,
                "tags": process.tags,
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
    container: Optional[str],
    cwd: Optional[str],
    display_name: Optional[str],
    tags: Optional[str],
) -> None:
    """Define a new process."""
    from .db import get_database
    from .models import ContextType, ProcessDefinition

    if context == "docker" and not container:
        output_json(
            error_response(
                "Container name required for docker context",
                error_code="missing_container",
                suggestion="Use --container <name> to specify the Docker container",
            )
        )
        sys.exit(1)

    db = get_database()

    # Check if process already exists
    existing = db.get_process_by_name(name)
    if existing:
        output_json(
            error_response(
                f"Process '{name}' already exists",
                error_code="process_exists",
                suggestion=f"Use 'procgler remove {name}' first, or choose a different name",
            )
        )
        sys.exit(1)

    tag_list = [t.strip() for t in tags.split(",")] if tags else []

    process = ProcessDefinition(
        id=0,  # Will be set by database
        name=name,
        command=cmd,
        context_type=ContextType(context),
        display_name=display_name,
        container_name=container,
        cwd=cwd,
        tags=tag_list,
    )

    created = db.create_process(process)

    output_json(
        success_response(
            {
                "action": "created",
                "process": {
                    "id": created.id,
                    "name": created.name,
                    "command": created.command,
                    "context_type": created.context_type.value,
                },
            }
        )
    )


@cli.command()
@click.argument("name")
def remove(name: str) -> None:
    """Remove a process definition."""
    from .db import get_database

    db = get_database()

    if not db.get_process_by_name(name):
        output_json(
            error_response(
                f"Process '{name}' not found",
                error_code="process_not_found",
                suggestion="Run 'procgler list' to see available processes",
            )
        )
        sys.exit(1)

    db.delete_process(name)
    output_json(success_response({"action": "removed", "name": name}))


@cli.command()
@click.argument("name")
def start(name: str) -> None:
    """Start a process (idempotent - no-op if running)."""
    # Placeholder for Phase 2
    output_json(
        error_response(
            "Process management not yet implemented",
            error_code="not_implemented",
            suggestion="This feature will be available in Phase 2",
        )
    )
    sys.exit(1)


@cli.command()
@click.argument("name")
def stop(name: str) -> None:
    """Stop a process (idempotent - no-op if stopped)."""
    # Placeholder for Phase 2
    output_json(
        error_response(
            "Process management not yet implemented",
            error_code="not_implemented",
            suggestion="This feature will be available in Phase 2",
        )
    )
    sys.exit(1)


@cli.command()
@click.argument("name")
def restart(name: str) -> None:
    """Restart a process (stop then start)."""
    # Placeholder for Phase 2
    output_json(
        error_response(
            "Process management not yet implemented",
            error_code="not_implemented",
            suggestion="This feature will be available in Phase 2",
        )
    )
    sys.exit(1)


@cli.command()
@click.argument("name")
@click.option("--tail", default=100, help="Number of lines to return")
@click.option("--since", help="Time filter (e.g., '5m', '1h', ISO timestamp)")
def logs(name: str, tail: int, since: Optional[str]) -> None:
    """Get logs for a process."""
    # Placeholder for Phase 3
    output_json(
        error_response(
            "Log retrieval not yet implemented",
            error_code="not_implemented",
            suggestion="This feature will be available in Phase 3",
        )
    )
    sys.exit(1)


if __name__ == "__main__":
    cli()
