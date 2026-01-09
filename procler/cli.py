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


# CLI schema for capabilities command - LLM-friendly discovery

CLI_SCHEMA = {
    "name": "procler",
    "version": __version__,
    "description": "LLM-first process manager for developers. All output is JSON.",
    "output_format": "All commands return JSON with {success: bool, data?: object, error?: string, error_code?: string, suggestion?: string}",
    "config_location": ".procler/ directory (per-project, version-controllable)",
    "common_workflows": [
        {
            "name": "Start a dev environment",
            "steps": ["procler group start backend", "procler status"],
            "description": "Start all backend processes in order and verify status",
        },
        {
            "name": "Graceful restart with migration",
            "steps": ["procler recipe run deploy --dry-run", "procler recipe run deploy"],
            "description": "Preview then execute a multi-step deployment recipe",
        },
        {
            "name": "Debug a failing process",
            "steps": ["procler status api", "procler logs api --tail 50", "procler restart api"],
            "description": "Check status, view recent logs, then restart",
        },
        {
            "name": "Initialize a new project",
            "steps": ["procler config init", "# Edit .procler/config.yaml", "procler config validate"],
            "description": "Create config directory with template, then validate",
        },
    ],
    "commands": {
        "capabilities": {
            "description": "Returns JSON schema of all commands (LLM discovery)",
            "example": "procler capabilities",
            "arguments": [],
            "options": [],
        },
        "help-llm": {
            "description": "Output comprehensive LLM-focused usage instructions in markdown format",
            "example": "procler help-llm",
            "arguments": [],
            "options": [],
        },
        "status": {
            "description": "Show status of all processes or a specific one",
            "example": "procler status api",
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
            "example": "procler start api",
            "arguments": [
                {"name": "name", "required": True, "description": "Process name"}
            ],
            "options": [],
        },
        "stop": {
            "description": "Stop a process (idempotent - no-op if stopped)",
            "example": "procler stop api",
            "arguments": [
                {"name": "name", "required": True, "description": "Process name"}
            ],
            "options": [],
        },
        "restart": {
            "description": "Restart a process (stop then start)",
            "example": "procler restart api",
            "arguments": [
                {"name": "name", "required": True, "description": "Process name"}
            ],
            "options": [],
        },
        "define": {
            "description": "Define a new process in runtime DB (prefer config.yaml for persistence)",
            "example": "procler define --name api --command 'uvicorn main:app' --cwd /app",
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
            "description": "Remove a process definition from runtime DB",
            "example": "procler remove api",
            "arguments": [
                {"name": "name", "required": True, "description": "Process name"}
            ],
            "options": [],
        },
        "list": {
            "description": "List all process definitions",
            "example": "procler list",
            "arguments": [],
            "options": [],
        },
        "logs": {
            "description": "Get logs for a process",
            "example": "procler logs api --tail 50 --since 5m",
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
            "description": "Execute an arbitrary command (one-off, not a managed process)",
            "example": "procler exec 'ls -la' --context docker --container myapp",
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
            "description": "Manage command snippets (reusable one-off commands)",
            "subcommands": {
                "list": {
                    "description": "List all snippets",
                    "example": "procler snippet list --tag docker",
                    "options": [
                        {"name": "--tag", "required": False, "description": "Filter by tag"}
                    ],
                },
                "save": {
                    "description": "Save a new snippet",
                    "example": "procler snippet save --name rebuild --command 'docker compose build'",
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
                    "example": "procler snippet run rebuild",
                    "arguments": [
                        {"name": "name", "required": True, "description": "Snippet name"}
                    ],
                },
                "remove": {
                    "description": "Remove a snippet",
                    "example": "procler snippet remove rebuild",
                    "arguments": [
                        {"name": "name", "required": True, "description": "Snippet name"}
                    ],
                },
            },
        },
        "serve": {
            "description": "Start the web server (API + optional Vue dashboard)",
            "example": "procler serve --port 8000 --reload",
            "arguments": [],
            "options": [
                {"name": "--host", "required": False, "default": "127.0.0.1", "description": "Host to bind"},
                {"name": "--port", "required": False, "default": 8000, "description": "Port to bind"},
                {"name": "--reload", "required": False, "is_flag": True, "description": "Enable hot reload"},
            ],
        },
        "group": {
            "description": "Manage process groups (ordered start/stop from config.yaml)",
            "subcommands": {
                "list": {
                    "description": "List all groups defined in config",
                    "example": "procler group list",
                },
                "start": {
                    "description": "Start all processes in a group (in defined order)",
                    "example": "procler group start backend",
                    "arguments": [
                        {"name": "name", "required": True, "description": "Group name"}
                    ],
                },
                "stop": {
                    "description": "Stop all processes in a group (in reverse/custom order)",
                    "example": "procler group stop backend",
                    "arguments": [
                        {"name": "name", "required": True, "description": "Group name"}
                    ],
                },
                "status": {
                    "description": "Get status of all processes in a group",
                    "example": "procler group status backend",
                    "arguments": [
                        {"name": "name", "required": True, "description": "Group name"}
                    ],
                },
            },
        },
        "recipe": {
            "description": "Manage and run recipes (multi-step operations from config.yaml)",
            "subcommands": {
                "list": {
                    "description": "List all recipes defined in config",
                    "example": "procler recipe list",
                },
                "show": {
                    "description": "Show recipe details and steps",
                    "example": "procler recipe show deploy",
                    "arguments": [
                        {"name": "name", "required": True, "description": "Recipe name"}
                    ],
                },
                "run": {
                    "description": "Execute a recipe (use --dry-run to preview)",
                    "example": "procler recipe run deploy --dry-run",
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
            "description": "Manage configuration (.procler/ directory)",
            "subcommands": {
                "init": {
                    "description": "Initialize .procler/ config directory with template",
                    "example": "procler config init",
                },
                "validate": {
                    "description": "Validate config.yaml syntax and all references",
                    "example": "procler config validate",
                },
                "path": {
                    "description": "Show the resolved config directory path",
                    "example": "procler config path",
                },
                "explain": {
                    "description": "Explain what the config defines in plain language (LLM-friendly)",
                    "example": "procler config explain",
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


@cli.command("help-llm")
def help_llm() -> None:
    """Output comprehensive LLM-focused usage instructions."""
    instructions = """# Procler - LLM-First Process Manager

## Overview
Procler is a process manager designed for LLM integration. All CLI commands return structured JSON with a consistent response format:
- `success`: boolean indicating operation result
- `data`: payload on success
- `error`: error message on failure
- `error_code`: machine-readable error identifier
- `suggestion`: actionable fix for errors

## Quick Start

### 1. Discover Commands
```bash
procler capabilities  # JSON schema of all commands
procler --help        # Human-readable help
```

### 2. Initialize Config
```bash
procler config init      # Creates .procler/ directory
procler config validate  # Validates config.yaml
procler config explain   # Plain-language explanation
```

### 3. Process Management
```bash
procler define --name api --command 'uvicorn main:app' --cwd /app
procler start api        # Idempotent - safe to retry
procler stop api         # Idempotent - safe to retry
procler restart api      # Stop then start
procler restart api --clear-logs  # Clear logs on restart
procler status api       # Get process status with Linux state
procler logs api --tail 50
```

### 4. Groups (Ordered Start/Stop)
```bash
procler group list
procler group start backend   # Starts in order, waits for dependencies
procler group stop backend    # Stops in reverse order
procler group status backend
```

### 5. Recipes (Multi-Step Operations)
```bash
procler recipe list
procler recipe show deploy
procler recipe run deploy --dry-run    # Preview
procler recipe run deploy              # Execute
```

### 6. Snippets (Reusable Commands)
```bash
procler snippet list
procler snippet save --name rebuild --command 'docker compose build'
procler snippet run rebuild
```

## Response Format

### Success Response
```json
{
  "success": true,
  "data": { ... }
}
```

### Error Response
```json
{
  "success": false,
  "error": "Process 'api' not found",
  "error_code": "process_not_found",
  "suggestion": "Run 'procler list' to see available processes"
}
```

## Process Status Fields
- `status`: "running" | "stopped" | "failed"
- `pid`: Process ID (null if stopped)
- `uptime_seconds`: Time since start
- `linux_state`: Linux kernel state (R, S, D, Z, T)
  - D state = "uninterruptible sleep" - process cannot be killed
  - Z state = "zombie" - terminated but not reaped
- `warning`: Alert for problematic states

## Config File (.procler/config.yaml)

```yaml
version: 1

processes:
  api:
    command: uvicorn main:app --reload
    context: local  # or docker
    container: my-container  # if docker
    cwd: /path/to/project
    tags: [backend, api]
    healthcheck:
      test: "curl -f http://localhost:8000/health"
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 30s
    depends_on:
      - redis           # Wait for started
      - name: database
        condition: healthy  # Wait for health check

groups:
  backend:
    processes: [redis, database, api]
    stop_order: [api, database, redis]  # Optional

recipes:
  deploy:
    on_error: stop  # or continue
    steps:
      - stop: api
      - exec: "alembic upgrade head"
      - start: api

snippets:
  rebuild:
    command: docker compose build
    tags: [docker]
```

## Common Workflows

### Start Development Environment
```bash
procler group start backend && procler status
```

### Debug Failing Process
```bash
procler status api
procler logs api --tail 100
procler restart api --clear-logs
```

### Graceful Deployment
```bash
procler recipe run deploy --dry-run
procler recipe run deploy
```

## Web Server

```bash
procler serve --port 8000 --reload  # Development
procler serve --host 0.0.0.0        # Production
```

REST API: http://localhost:8000/api
WebSocket: ws://localhost:8000/api/ws
OpenAPI: http://localhost:8000/api/docs

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| PROCLER_LOG_LEVEL | INFO | Log level (DEBUG, INFO, WARNING, ERROR) |
| PROCLER_LOG_FILE | - | Log file path (auto-rotates) |
| PROCLER_CONFIG_DIR | .procler/ | Config directory |
| PROCLER_DEBUG | - | Enable detailed error messages |

## Exit Codes
- 0: Success
- 1: Operation failed (see error in JSON output)
"""
    # Output as JSON with the instructions as a field
    output_json(success_response({
        "format": "markdown",
        "instructions": instructions.strip(),
        "tip": "Parse 'instructions' field for LLM consumption or pipe to less/cat for human reading"
    }))


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
@click.option("--clear-logs", is_flag=True, help="Delete old logs before restarting")
def restart(name: str, clear_logs: bool) -> None:
    """Restart a process (stop then start)."""
    import asyncio

    from .core import get_process_manager

    manager = get_process_manager()
    result = asyncio.run(manager.restart(name, clear_logs=clear_logs))

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


@config.command("explain")
def config_explain() -> None:
    """Explain what the config defines in plain language (LLM-friendly)."""
    from .config import get_config, get_config_file_path

    cfg = get_config()
    config_path = get_config_file_path()

    if not config_path.exists():
        output_json(
            success_response(
                {
                    "summary": "No config file found. Run 'procler config init' to create one.",
                    "sections": [],
                }
            )
        )
        return

    sections = []

    # Explain processes
    if cfg.processes:
        proc_explanations = []
        for name, proc in cfg.processes.items():
            ctx = "locally" if proc.context.value == "local" else f"in Docker container '{proc.container}'"
            desc = f"'{name}': runs `{proc.command}` {ctx}"
            if proc.cwd:
                desc += f" (working dir: {proc.cwd})"
            if proc.description:
                desc += f" - {proc.description}"
            proc_explanations.append(desc)
        sections.append({
            "type": "processes",
            "title": f"{len(cfg.processes)} Process Definitions",
            "explanation": "These processes can be started, stopped, and monitored individually.",
            "items": proc_explanations,
        })

    # Explain groups
    if cfg.groups:
        group_explanations = []
        for name, group in cfg.groups.items():
            stop_order = group.get_stop_order()
            is_reversed = stop_order == list(reversed(group.processes))
            stop_desc = "reversed order" if is_reversed else f"custom order: {' -> '.join(stop_order)}"
            desc = f"'{name}': starts [{' -> '.join(group.processes)}], stops in {stop_desc}"
            if group.description:
                desc += f" - {group.description}"
            group_explanations.append(desc)
        sections.append({
            "type": "groups",
            "title": f"{len(cfg.groups)} Process Groups",
            "explanation": "Groups start processes in order and stop them in reverse (or custom) order.",
            "items": group_explanations,
        })

    # Explain recipes
    if cfg.recipes:
        recipe_explanations = []
        for name, recipe in cfg.recipes.items():
            steps = recipe.get_steps()
            step_summary = f"{len(steps)} steps"
            error_handling = "stops on error" if recipe.on_error.value == "stop" else "continues on error"
            desc = f"'{name}': {step_summary}, {error_handling}"
            if recipe.description:
                desc += f" - {recipe.description}"
            recipe_explanations.append(desc)
        sections.append({
            "type": "recipes",
            "title": f"{len(cfg.recipes)} Recipes",
            "explanation": "Recipes are multi-step operations that automate common workflows.",
            "items": recipe_explanations,
        })

    # Explain snippets
    if cfg.snippets:
        snippet_explanations = []
        for name, snippet in cfg.snippets.items():
            ctx = "locally" if snippet.context.value == "local" else f"in Docker '{snippet.container}'"
            desc = f"'{name}': `{snippet.command}` ({ctx})"
            if snippet.description:
                desc += f" - {snippet.description}"
            snippet_explanations.append(desc)
        sections.append({
            "type": "snippets",
            "title": f"{len(cfg.snippets)} Snippets",
            "explanation": "Snippets are reusable commands you can run quickly.",
            "items": snippet_explanations,
        })

    # Build summary
    total = len(cfg.processes) + len(cfg.groups) + len(cfg.recipes) + len(cfg.snippets)
    summary = f"Config defines {total} items: {len(cfg.processes)} processes, {len(cfg.groups)} groups, {len(cfg.recipes)} recipes, {len(cfg.snippets)} snippets."

    output_json(
        success_response(
            {
                "summary": summary,
                "sections": sections,
                "config_file": str(config_path),
            }
        )
    )


if __name__ == "__main__":
    cli()
