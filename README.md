# Procler

[日本語](README.ja.md)

<p align="center">
  <img src="procler.png" alt="Procler logo" width="160" height="160" />
</p>

[![PyPI version](https://img.shields.io/pypi/v/procler.svg)](https://pypi.org/project/procler/)
[![Python versions](https://img.shields.io/pypi/pyversions/procler.svg)](https://pypi.org/project/procler/)
[![CI](https://github.com/gabu-quest/procler/actions/workflows/ci.yml/badge.svg)](https://github.com/gabu-quest/procler/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

**A process manager where Claude Code is a first-class citizen.**

Procler gives developers (and their AI coding assistants) a single pane of glass for managing the chaos of modern development environments - where processes span local shells, Docker containers, and various execution contexts.

## Features

- **LLM-First CLI** - JSON-native commands designed for Claude Code integration
- **Web Dashboard** - Vue 3 dashboard with Cyberpunk design system, real-time updates
- **Dual Interface Parity** - CLI and Web UI share the same ProcessManager core
- **Context Abstraction** - Manage local processes and Docker containers uniformly
- **Groups & Recipes** - Orchestrate multi-process workflows with dependencies
- **Health Checks** - Monitor process health with configurable checks
- **Snippets** - Save and reuse common commands with tagging
- **Real-time Updates** - WebSocket support for live status and log streaming
- **Config Variables** - Define `vars` in config.yaml and reference with `${VAR}`

## Demo

<!-- TODO: Replace with actual recordings -->
<!-- Record with: asciinema rec demo.cast -->
<!-- Convert to GIF with: agg demo.cast demo.gif -->

<details>
<summary>Basic Workflow (define, start, status, logs, stop)</summary>

```
Coming soon - terminal recording
```
</details>

<details>
<summary>Group Start with Dependency Ordering</summary>

```
Coming soon - terminal recording
```
</details>

<details>
<summary>Recipe Dry-Run and Execution</summary>

```
Coming soon - terminal recording
```
</details>

## How Does Procler Compare?

| Feature | Procler | Process Compose | PM2 | Supervisord | Foreman |
|---------|:-------:|:---------------:|:---:|:-----------:|:-------:|
| LLM-first JSON CLI | ✅ | - | - | - | - |
| Web Dashboard (free) | ✅ | - | paid | - | - |
| Docker container execution | ✅ | - | bolt-on | - | - |
| Health checks | ✅ | ✅ | - | - | - |
| Dependency-ordered startup | ✅ | ✅ | - | - | - |
| `log_ready` condition | ✅ | ✅ | - | - | - |
| Multi-step recipes | ✅ | - | - | - | - |
| Snippets (command library) | ✅ | - | - | - | - |
| Audit trail | ✅ | - | - | - | - |
| WebSocket real-time | ✅ | - | - | - | - |
| Config explain (LLM) | ✅ | - | - | - | - |
| Memory threshold restart | ✅ | - | ✅ | - | - |
| HTTP/TCP readiness probes | ✅ | ✅ | - | - | - |
| Export to systemd | ✅ | - | - | - | ✅ |
| Cron/scheduled processes | ✅ | ✅ | - | - | - |
| Process replicas | ✅ | ✅ | ✅ | - | - |
| Procfile import | ✅ | - | - | - | ✅ |
| TUI mode | ✅ | ✅ | - | - | - |
| Language-agnostic | ✅ | ✅ | Node.js | Python | Ruby |

## Installation

```bash
# Recommended: install as a global tool
uv tool install procler

# Or via pip
pip install procler
```

Or install from source:

```bash
git clone https://github.com/gabu-quest/procler.git
cd procler
uv sync --all-extras
```

> **Note:** Frontend is pre-built and included. No separate build step needed!

## Quick Start

### Initialize Configuration

```bash
# Create .procler/ config directory
procler config init

# Validate your config
procler config validate

# Get a plain-language explanation of your config
procler config explain
```

### Process Management

```bash
# Define a process
procler define --name my-api --command "uvicorn main:app --port 8000"

# Start it
procler start my-api

# Check status (JSON output)
procler status my-api

# View logs
procler logs my-api --tail 50 --since 5m

# Stop it
procler stop my-api

# Restart (with optional log clearing)
procler restart my-api --clear-logs
```

### Docker Processes

```bash
# Define a process that runs in a Docker container
procler define \
  --name db-migrate \
  --command "alembic upgrade head" \
  --context docker \
  --container api-container

# Execute arbitrary command in container
procler exec "pip list" --context docker --container api-container
```

### Groups & Recipes

```bash
# Start all processes in a group (respects order and dependencies)
procler group start backend

# Stop in reverse order
procler group stop backend

# Preview a recipe before running
procler recipe run deploy --dry-run

# Execute the recipe
procler recipe run deploy
```

### Variable Substitution

Define vars in `.procler/config.yaml` and reference them in commands and container names:

```yaml
vars:
  SIM_CONTAINER: my-sim-container
  SIM_USER: "1000"
  SIM_WORKDIR: /opt/sim

processes:
  simulator:
    command: "${SIM_WORKDIR}/bin/simulator"
    context: docker
    container: "${SIM_CONTAINER}"
```

### Snippets (Reusable Commands)

```bash
# Save a snippet
procler snippet save \
  --name rebuild-api \
  --command "docker compose build api" \
  --tags docker,build

# List snippets (with optional tag filter)
procler snippet list --tag docker

# Run a snippet
procler snippet run rebuild-api
```

### Web Server

```bash
# Start the API server
procler serve --host 0.0.0.0 --port 8000

# With hot reload for development
procler serve --reload
```

## CLI Reference

All CLI commands return structured JSON for easy parsing by scripts and LLMs.

### Discovery & Config Commands

| Command | Description |
|---------|-------------|
| `procler capabilities` | Returns JSON schema of all commands (LLM discovery) |
| `procler help-llm` | Output comprehensive LLM-focused usage instructions |
| `procler config init [--force]` | Initialize `.procler/` config directory with template |
| `procler config validate` | Validate config.yaml syntax and all references |
| `procler config path` | Show the resolved config directory path |
| `procler config explain` | Explain config in plain language (LLM-friendly) |

### Process Commands

| Command | Description |
|---------|-------------|
| `procler define --name NAME --command CMD [options]` | Define a new process |
| `procler start NAME` | Start a process (idempotent) |
| `procler stop NAME` | Stop a process (idempotent) |
| `procler restart NAME [--clear-logs]` | Restart a process |
| `procler status [NAME]` | Show status (all or single process) |
| `procler list [--resolve]` | List all process definitions |
| `procler remove NAME` | Remove a process definition |
| `procler logs NAME [--tail N] [--since TIME] [-f]` | Get/follow logs |
| `procler exec "CMD" [--context TYPE] [--container NAME]` | Execute one-off command |

#### Define Options

| Option | Description |
|--------|-------------|
| `--name` | Process name (required) |
| `--command` | Command to execute (required) |
| `--context` | `local` or `docker` (default: local) |
| `--container` | Docker container name (required for docker) |
| `--cwd` | Working directory |
| `--display-name` | Human-friendly name |
| `--tags` | Comma-separated tags |
| `--daemon-mode` | Enable daemon mode (process forks) |
| `--daemon-pattern` | Process name pattern to match daemon |
| `--daemon-pidfile` | Path to daemon pidfile |
| `--force` | Overwrite existing definition |

### Group Commands

| Command | Description |
|---------|-------------|
| `procler group list` | List all groups defined in config |
| `procler group start NAME` | Start all processes in order |
| `procler group stop NAME` | Stop all processes in reverse/custom order |
| `procler group status NAME` | Get status of all processes in group |

### Recipe Commands

| Command | Description |
|---------|-------------|
| `procler recipe list` | List all recipes defined in config |
| `procler recipe show NAME` | Show recipe details and steps |
| `procler recipe run NAME [--dry-run] [--continue-on-error]` | Execute a recipe |

### Snippet Commands

| Command | Description |
|---------|-------------|
| `procler snippet list [--tag TAG]` | List all snippets |
| `procler snippet show NAME` | Show snippet details |
| `procler snippet save --name NAME --command CMD [options]` | Save a new snippet |
| `procler snippet run NAME` | Run a saved snippet |
| `procler snippet remove NAME` | Remove a snippet |

### Server Commands

| Command | Description |
|---------|-------------|
| `procler serve [--host HOST] [--port PORT] [--reload]` | Start the web server |

## Configuration

Procler uses a per-project `.procler/` directory:

```
.procler/
├── config.yaml    # Definitions (commit to git)
├── changelog.log  # Audit trail (commit to git)
└── state.db       # Runtime state (auto-gitignored)
```

**Discovery order:** `$PROCLER_CONFIG_DIR` → `.procler.env` → `.procler/` → git root → `~/.procler/`

### Example Configuration

```yaml
version: 1

vars:
  API_PORT: "8000"
  DB_CONTAINER: postgres-dev

processes:
  api:
    command: uvicorn main:app --reload --port ${API_PORT}
    context: local
    cwd: /path/to/project
    tags: [backend, api]
    description: "API server"
    healthcheck:
      test: "curl -f http://localhost:${API_PORT}/health"
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 30s

  worker:
    command: celery worker -A tasks
    context: local
    depends_on:
      - redis
      - name: api
        condition: healthy  # Wait for health check

  db-migrate:
    command: alembic upgrade head
    context: docker
    container: ${DB_CONTAINER}

groups:
  backend:
    description: "Full backend stack"
    processes: [redis, api, worker]
    stop_order: [worker, api, redis]  # Optional custom order

recipes:
  deploy:
    description: "Graceful deployment"
    on_error: stop  # or continue
    steps:
      - stop: worker
      - stop: api
      - wait: 2s
      - exec: "alembic upgrade head"
        context: docker
        container: ${DB_CONTAINER}
      - start: api
      - start: worker

snippets:
  rebuild:
    command: docker compose build
    description: "Rebuild containers"
    tags: [docker]
```

## CLI Output Format

All CLI commands return structured JSON:

### Success Response

```json
{
  "success": true,
  "data": {
    "processes": [
      {
        "name": "my-api",
        "status": "running",
        "pid": 12345,
        "uptime_seconds": 3600
      }
    ]
  }
}
```

### Error Response

```json
{
  "success": false,
  "error": "Container 'db-postgres' not found",
  "error_code": "container_not_found",
  "suggestion": "Run 'docker ps -a' to list available containers"
}
```

## REST API

Base URL: `http://localhost:8000/api`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/processes` | GET | List all processes |
| `/api/processes` | POST | Create process |
| `/api/processes/{name}` | GET | Get process |
| `/api/processes/{name}` | DELETE | Remove process |
| `/api/processes/{name}/start` | POST | Start process |
| `/api/processes/{name}/stop` | POST | Stop process |
| `/api/processes/{name}/restart` | POST | Restart process |
| `/api/logs/{name}` | GET | Get logs (?tail=100&since=5m) |
| `/api/groups` | GET | List all groups |
| `/api/groups/{name}/start` | POST | Start group |
| `/api/groups/{name}/stop` | POST | Stop group |
| `/api/groups/{name}/status` | GET | Group status |
| `/api/recipes` | GET | List all recipes |
| `/api/recipes/{name}/run` | POST | Run recipe |
| `/api/snippets` | GET | List snippets (?tag=filter) |
| `/api/snippets` | POST | Create snippet |
| `/api/snippets/{name}` | GET | Get snippet |
| `/api/snippets/{name}` | DELETE | Remove snippet |
| `/api/snippets/{name}/run` | POST | Run snippet |
| `/api/config` | GET | Config status |
| `/api/config/reload` | POST | Reload config |
| `/api/health` | GET | Health check |

## WebSocket

Connect to `ws://localhost:8000/api/ws` for real-time updates.

```javascript
// Subscribe to logs for a process
ws.send(JSON.stringify({action: "subscribe_logs", process_id: 1}));

// Subscribe to status updates (all processes)
ws.send(JSON.stringify({action: "subscribe_status"}));

// Receive updates
// {"type": "log", "process_id": 1, "data": {"line": "...", "stream": "stdout"}}
// {"type": "status", "process_id": 1, "data": {"status": "running", "pid": 123}}
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.12+, FastAPI |
| Database | SQLite via [sqler](https://pypi.org/project/sqler/) |
| Frontend | Vue 3, Vite, Pinia, Naive UI |
| CLI | Click |
| Docker | docker-py SDK |
| Real-time | WebSockets |

## Development

```bash
# Install dev dependencies
uv pip install -e .[dev]

# Run tests (154 tests)
uv run pytest -v

# Run CLI in development
uv run procler --help

# Run server with hot reload
uv run procler serve --reload

# Rebuild frontend (only if modifying Vue code)
bash scripts/build_frontend.sh
```

### Pre-commit Hooks

This project uses pre-commit hooks for code quality. Install them with:

```bash
pre-commit install
```

The hooks run ruff for linting and formatting on every commit.

## Web Dashboard

The Vue 3 frontend provides a visual interface for managing processes and snippets:

- **Dashboard** - Overview of all processes with real-time status
- **Process List** - View all defined processes with start/stop/restart controls, per-action loading states
- **Process Detail** - Live log streaming via WebSocket with search/filter and stream filtering
- **Groups** - Card-based view with one-click start/stop all
- **Recipes** - Step preview, dry-run, execution progress
- **Snippets** - Save, manage, and run reusable commands with confirmations
- **Config** - Status, stats, variable display, changelog viewer

### Keyboard Shortcuts

Press `?` to view all shortcuts. Quick navigation:
- `g d` - Dashboard
- `g p` - Processes
- `g g` - Groups
- `g r` - Recipes
- `g s` - Snippets
- `g c` - Config
- `g a` - About

### UX Features

- **Connection Status** - WebSocket indicator in header shows connected/connecting/error states
- **Toast Notifications** - Automatic notifications when process status changes
- **Log Search** - Filter logs by text (with match highlighting) or stream (stdout/stderr)
- **Breadcrumbs** - Navigation context on detail pages
- **Confirmations** - Destructive actions require confirmation

### Running the Dashboard

```bash
# Start the server (serves both API and web UI)
uv run procler serve --port 8000
```

Open http://localhost:8000 to access the dashboard.

> **Frontend Development:** For Vue development, run `cd frontend && npm run dev` (dev server on port 5173) and rebuild with `bash scripts/build_frontend.sh`

## Claude Code Integration

Procler is designed for seamless AI assistant integration:

```
Human: "My auth-api seems slow, check its recent logs and restart it if there are errors"

Claude Code:
1. procler logs auth-api --tail 100
2. [Analyzes JSON log output]
3. procler restart auth-api
4. procler status auth-api
5. Reports back to human
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PROCLER_LOG_LEVEL` | `INFO` | Log level (DEBUG, INFO, WARNING, ERROR) |
| `PROCLER_LOG_FILE` | - | Log file path (auto-rotates) |
| `PROCLER_CONFIG_DIR` | `.procler/` | Config directory |
| `PROCLER_DB_PATH` | `.procler/state.db` | Database path |
| `PROCLER_CORS_ORIGINS` | `localhost` | Comma-separated allowed origins |
| `PROCLER_DEBUG` | - | Enable detailed error messages |

## License

MIT
