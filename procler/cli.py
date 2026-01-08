"""CLI interface for Procler."""

import json
import sys
from datetime import datetime
from pathlib import Path
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
    "name": "procler",
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
        "group": {
            "description": "Manage process groups",
            "subcommands": {
                "list": {
                    "description": "List all groups",
                },
                "start": {
                    "description": "Start all processes in a group (in order)",
                    "arguments": [
                        {"name": "name", "required": True, "description": "Group name"}
                    ],
                },
                "stop": {
                    "description": "Stop all processes in a group (in reverse order)",
                    "arguments": [
                        {"name": "name", "required": True, "description": "Group name"}
                    ],
                },
                "status": {
                    "description": "Get status of all processes in a group",
                    "arguments": [
                        {"name": "name", "required": True, "description": "Group name"}
                    ],
                },
            },
        },
        "recipe": {
            "description": "Manage and run recipes (multi-step operations)",
            "subcommands": {
                "list": {
                    "description": "List all recipes",
                },
                "show": {
                    "description": "Show recipe details and steps",
                    "arguments": [
                        {"name": "name", "required": True, "description": "Recipe name"}
                    ],
                },
                "run": {
                    "description": "Execute a recipe",
                    "arguments": [
                        {"name": "name", "required": True, "description": "Recipe name"}
                    ],
                    "options": [
                        {"name": "--dry-run", "required": False, "is_flag": True, "description": "Show what would happen without executing"},
                        {"name": "--continue-on-error", "required": False, "is_flag": True, "description": "Continue execution even if a step fails"},
                    ],
                },
            },
        },
        "config": {
            "description": "Manage configuration",
            "subcommands": {
                "init": {
                    "description": "Initialize .procler/ config directory with template",
                },
                "validate": {
                    "description": "Validate config.yaml syntax and references",
                },
                "path": {
                    "description": "Show the config directory path",
                },
            },
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
@click.version_option(version=__version__, prog_name="procler")
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
                suggestion=f"Use 'procler remove {name}' first, or choose a different name",
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
                suggestion="Run 'procler list' to see available processes",
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


# Snippet subcommands
@cli.group()
def snippet() -> None:
    """Manage command snippets."""
    pass


@snippet.command("list")
@click.option("--tag", help="Filter by tag")
def snippet_list(tag: str | None) -> None:
    """List all snippets."""
    from .core import get_snippet_manager

    manager = get_snippet_manager()
    result = manager.list_snippets(tag=tag)

    output_json(result)


@snippet.command("save")
@click.option("--name", required=True, help="Snippet name")
@click.option("--command", "cmd", required=True, help="Command to save")
@click.option("--description", help="Description of what the snippet does")
@click.option(
    "--context",
    type=click.Choice(["local", "docker"]),
    default="local",
    help="Execution context",
)
@click.option("--container", help="Docker container name (required if context=docker)")
@click.option("--tags", help="Comma-separated tags")
def snippet_save(
    name: str,
    cmd: str,
    description: str | None,
    context: str,
    container: str | None,
    tags: str | None,
) -> None:
    """Save a new snippet."""
    from .core import get_snippet_manager

    if context == "docker" and not container:
        output_json(
            error_response(
                "Container name required for docker context",
                error_code="missing_container",
                suggestion="Use --container <name> to specify the Docker container",
            )
        )
        sys.exit(1)

    tag_list = [t.strip() for t in tags.split(",")] if tags else None

    manager = get_snippet_manager()
    result = manager.save_snippet(
        name=name,
        command=cmd,
        description=description,
        context_type=context,
        container_name=container,
        tags=tag_list,
    )

    output_json(result)
    if not result["success"]:
        sys.exit(1)


@snippet.command("run")
@click.argument("name")
def snippet_run(name: str) -> None:
    """Run a saved snippet."""
    import asyncio

    from .core import get_snippet_manager

    manager = get_snippet_manager()
    result = asyncio.run(manager.run_snippet(name))

    output_json(result)
    if not result["success"]:
        sys.exit(1)


@snippet.command("remove")
@click.argument("name")
def snippet_remove(name: str) -> None:
    """Remove a snippet."""
    from .core import get_snippet_manager

    manager = get_snippet_manager()
    result = manager.remove_snippet(name)

    output_json(result)
    if not result["success"]:
        sys.exit(1)


@cli.command()
@click.option("--host", default="127.0.0.1", help="Host to bind")
@click.option("--port", default=8000, help="Port to bind")
@click.option("--reload", is_flag=True, help="Enable hot reload")
def serve(host: str, port: int, reload: bool) -> None:
    """Start the web server."""
    import uvicorn

    from .db import init_database

    # Initialize database before starting server
    init_database()

    uvicorn.run(
        "procler.api:app",
        host=host,
        port=port,
        reload=reload,
    )


# Group subcommands
@cli.group()
def group() -> None:
    """Manage process groups (defined in config.yaml)."""
    pass


@group.command("list")
def group_list() -> None:
    """List all defined groups."""
    from .core import get_group_manager

    manager = get_group_manager()
    result = manager.list_groups()
    output_json(result)


@group.command("start")
@click.argument("name")
def group_start(name: str) -> None:
    """Start all processes in a group (in order)."""
    import asyncio

    from .core import get_group_manager

    manager = get_group_manager()
    result = asyncio.run(manager.start_group(name))

    output_json(result)
    if not result["success"]:
        sys.exit(1)


@group.command("stop")
@click.argument("name")
def group_stop(name: str) -> None:
    """Stop all processes in a group (in reverse order)."""
    import asyncio

    from .core import get_group_manager

    manager = get_group_manager()
    result = asyncio.run(manager.stop_group(name))

    output_json(result)
    if not result["success"]:
        sys.exit(1)


@group.command("status")
@click.argument("name")
def group_status(name: str) -> None:
    """Get status of all processes in a group."""
    import asyncio

    from .core import get_group_manager

    manager = get_group_manager()
    result = asyncio.run(manager.status_group(name))

    output_json(result)
    if not result["success"]:
        sys.exit(1)


# Recipe subcommands
@cli.group()
def recipe() -> None:
    """Manage and run recipes (multi-step operations)."""
    pass


@recipe.command("list")
def recipe_list() -> None:
    """List all defined recipes."""
    from .core import get_recipe_executor

    executor = get_recipe_executor()
    result = executor.list_recipes()
    output_json(result)


@recipe.command("show")
@click.argument("name")
def recipe_show(name: str) -> None:
    """Show recipe details and steps."""
    from .core import get_recipe_executor

    executor = get_recipe_executor()
    result = executor.get_recipe(name)

    output_json(result)
    if not result["success"]:
        sys.exit(1)


@recipe.command("run")
@click.argument("name")
@click.option("--dry-run", is_flag=True, help="Show what would happen without executing")
@click.option("--continue-on-error", is_flag=True, help="Continue execution even if a step fails")
def recipe_run(name: str, dry_run: bool, continue_on_error: bool) -> None:
    """Execute a recipe."""
    import asyncio

    from .core import get_recipe_executor

    executor = get_recipe_executor()

    # Only pass continue_on_error if explicitly set
    kwargs = {"dry_run": dry_run}
    if continue_on_error:
        kwargs["continue_on_error"] = True

    result = asyncio.run(executor.run_recipe(name, **kwargs))

    output_json(result)
    if not result["success"]:
        sys.exit(1)


# Config subcommands
@cli.group()
def config() -> None:
    """Manage configuration (config.yaml)."""
    pass


@config.command("init")
@click.option("--force", is_flag=True, help="Overwrite existing config")
def config_init(force: bool) -> None:
    """Initialize .procler/ config directory with template."""
    from .config import find_config_dir, generate_template_config, get_config_file_path

    config_dir = find_config_dir()
    config_file = config_dir / "config.yaml"

    # Create directory if needed
    config_dir.mkdir(parents=True, exist_ok=True)

    if config_file.exists() and not force:
        output_json(
            error_response(
                f"Config file already exists: {config_file}",
                error_code="config_exists",
                suggestion="Use --force to overwrite",
            )
        )
        sys.exit(1)

    # Write template
    template = generate_template_config()
    config_file.write_text(template)

    # Create .gitignore for state.db
    gitignore = config_dir / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text("# Runtime state - not version controlled\nstate.db\n")

    output_json(
        success_response(
            {
                "action": "initialized",
                "config_dir": str(config_dir),
                "config_file": str(config_file),
                "files_created": ["config.yaml", ".gitignore"],
            }
        )
    )


@config.command("validate")
def config_validate() -> None:
    """Validate config.yaml syntax and references."""
    from .config import load_config, get_config_file_path, reload_config

    config_path = get_config_file_path()

    if not config_path.exists():
        output_json(
            error_response(
                f"Config file not found: {config_path}",
                error_code="config_not_found",
                suggestion="Run 'procler config init' to create one",
            )
        )
        sys.exit(1)

    try:
        # Force reload to catch parse errors
        cfg = reload_config()
        errors = cfg.validate_references()

        if errors:
            output_json(
                error_response(
                    "Config validation failed",
                    error_code="validation_failed",
                    errors=errors,
                )
            )
            sys.exit(1)

        output_json(
            success_response(
                {
                    "valid": True,
                    "config_file": str(config_path),
                    "summary": {
                        "processes": len(cfg.processes),
                        "groups": len(cfg.groups),
                        "recipes": len(cfg.recipes),
                        "snippets": len(cfg.snippets),
                    },
                }
            )
        )

    except Exception as e:
        output_json(
            error_response(
                f"Failed to parse config: {e}",
                error_code="parse_error",
            )
        )
        sys.exit(1)


@config.command("path")
def config_path() -> None:
    """Show the config directory path."""
    from .config import find_config_dir, get_config_file_path, get_changelog_path, get_state_db_path

    config_dir = find_config_dir()

    output_json(
        success_response(
            {
                "config_dir": str(config_dir),
                "config_file": str(get_config_file_path()),
                "changelog": str(get_changelog_path()),
                "state_db": str(get_state_db_path()),
                "exists": {
                    "config_dir": config_dir.exists(),
                    "config_file": get_config_file_path().exists(),
                    "changelog": get_changelog_path().exists(),
                    "state_db": get_state_db_path().exists(),
                },
            }
        )
    )


if __name__ == "__main__":
    cli()
