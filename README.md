# Procler

**English | [日本語](README.ja.md)**

<p align="center">
  <img src="procler.png" alt="Procler logo" width="160" height="160" />
</p>

[![PyPI version](https://img.shields.io/pypi/v/procler.svg)](https://pypi.org/project/procler/)
[![Python versions](https://img.shields.io/pypi/pyversions/procler.svg)](https://pypi.org/project/procler/)
[![CI](https://github.com/gabu-quest/procler/actions/workflows/ci.yml/badge.svg)](https://github.com/gabu-quest/procler/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

**A process manager where Claude Code is a first-class citizen.**

Every command returns structured JSON. Every error includes a machine-readable code and a suggested fix. Built for the workflow where your AI assistant manages your dev environment.

## Quick Start

```bash
uv tool install procler

procler define --name api --command "uvicorn main:app --port 8000"
procler start api
procler status api       # JSON with pid, uptime, linux_state
procler logs api --tail 20
procler stop api
```

<!-- Record demos: bash scripts/record-demos.sh -->
<!-- Requires: asciinema (uv tool install asciinema) -->

## Why Procler?

Modern development means juggling local servers, Docker containers, background workers, and database migrations. Procler gives you one tool to manage all of them — with JSON output that LLMs can parse, health checks that block dependent services, and recipes that automate multi-step workflows.

## Features

**Core** — Process lifecycle with local and Docker execution contexts, log capture, PID tracking, Linux kernel state detection (`/proc` integration).

**Orchestration** — Groups with dependency-ordered startup (`depends_on` with `healthy`/`log_ready` conditions), multi-step recipes with dry-run preview, cron-scheduled processes, process replicas.

**Monitoring** — HTTP/TCP/command health probes, memory threshold auto-restart, `ready_log_line` regex matching, real-time WebSocket status and log streaming.

**Developer Experience** — JSON-native CLI, structured errors with `error_code` + `suggestion`, config variable substitution (`${VAR}`), Procfile import, systemd/Compose export, command snippets, Vue 3 web dashboard, Textual TUI.

## When to Use Procler

**Good fit:**
- Multi-service dev environments (API + worker + DB + cache)
- Mixed local + Docker workflows
- AI-assisted development (Claude Code, Cursor, etc.)
- Teams that want config-as-code for their dev processes

**Consider alternatives if:**
- Single-process monitoring only — use your OS process manager
- Kubernetes clusters — use Helm/ArgoCD
- Multi-machine orchestration — use Nomad or Docker Swarm
- Production deployment only — use systemd directly (Procler can export to it)

## Comparison

| Feature | Procler | Process Compose | PM2 | Supervisord | Foreman |
|---------|:-------:|:---------------:|:---:|:-----------:|:-------:|
| LLM-first JSON CLI | **yes** | - | - | - | - |
| Web dashboard (free) | **yes** | - | paid | - | - |
| Docker container exec | **yes** | - | bolt-on | - | - |
| Health checks (HTTP/TCP/cmd) | **yes** | **yes** | - | - | - |
| Dependency-ordered startup | **yes** | **yes** | - | - | - |
| `log_ready` condition | **yes** | **yes** | - | - | - |
| Multi-step recipes | **yes** | - | - | - | - |
| Command snippets | **yes** | - | - | - | - |
| Cron scheduling | **yes** | **yes** | - | - | - |
| Process replicas | **yes** | **yes** | **yes** | - | - |
| Memory threshold restart | **yes** | - | **yes** | - | - |
| Export to systemd/Compose | **yes** | - | - | - | **yes** |
| Procfile import | **yes** | - | - | - | **yes** |
| TUI mode | **yes** | **yes** | - | - | - |
| Audit trail | **yes** | - | - | - | - |
| Language-agnostic | **yes** | **yes** | Node.js | Python | Ruby |

## Showcase

### [C01] Basic Process Lifecycle

```bash
$ procler define --name my-api --command "sleep 60"
{
  "success": true,
  "data": {"action": "created", "process": {"name": "my-api", ...}}
}

$ procler start my-api
{
  "success": true,
  "data": {"status": "started", "process": {"status": "running", "pid": 12345}}
}

$ procler status my-api
{
  "success": true,
  "data": {"process": {"name": "my-api", "status": "running", "pid": 12345, "uptime_seconds": 5}}
}

$ procler stop my-api
{"success": true, "data": {"status": "stopped"}}
```

### [C02] JSON Response Contract

Every CLI command returns this envelope:

```json
{"success": true, "data": {"..."}}
```

### [C03] Error Response Contract

Every error includes `error_code` and `suggestion`:

```json
{
  "success": false,
  "error": "Process 'api' not found",
  "error_code": "process_not_found",
  "suggestion": "Run 'procler list' to see available processes"
}
```

### [C15] Idempotent Operations

```bash
$ procler start my-api       # Already running → no-op
{"success": true, "data": {"status": "already_running", "process": {"pid": 12345}}}

$ procler stop my-api        # Already stopped → no-op
{"success": true, "data": {"status": "already_stopped"}}
```

### [C04] Group Orchestration

```bash
$ procler group start backend  # Starts redis → db → api → worker (in order)
$ procler group status backend # Status of all group processes
$ procler group stop backend   # Stops in reverse order
```

### [C05] Recipe Dry-Run

```bash
$ procler recipe run deploy --dry-run   # Preview without executing
$ procler recipe run deploy             # Execute the multi-step recipe
```

### [C06] Snippet Lifecycle

```bash
$ procler snippet save --name rebuild --command "docker compose build" --tags docker
$ procler snippet list --tag docker
$ procler snippet run rebuild
$ procler snippet remove rebuild
```

## Installation

```bash
# Recommended
uv tool install procler

# With TUI support
uv tool install procler[tui]

# Or via pip
pip install procler
```

From source:

```bash
git clone https://github.com/gabu-quest/procler.git
cd procler && uv sync --all-extras
```

> Frontend is pre-built and included. No separate build step needed.

## Configuration

Per-project `.procler/` directory. Discovery order: `$PROCLER_CONFIG_DIR` > `.procler.env` > `.procler/` > git root > `~/.procler/`

```bash
procler config init       # [C07] Creates .procler/ with template
procler config validate   # [C08] Validates syntax and references
procler config explain    # Plain-language explanation (LLM-friendly)
```

### [C09] Comprehensive Example

```yaml
version: 1

vars:
  API_PORT: "8000"
  DB_CONTAINER: postgres-dev

processes:
  api:
    command: uvicorn main:app --reload --port ${API_PORT}     # Variable substitution
    context: local
    cwd: /path/to/project
    tags: [backend, api]
    description: "API server"
    namespace: backend                                         # Namespace isolation
    ready_log_line: "Uvicorn running on"                      # log_ready condition
    max_memory: 512M                                          # Auto-restart on RSS exceed
    healthcheck:
      http_get: "http://localhost:${API_PORT}/health"         # HTTP probe (built-in)
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 30s

  worker:
    command: celery worker -A tasks
    replicas: 3                                               # Creates worker-1, -2, -3
    depends_on:
      - redis                                                 # Wait for started (default)
      - name: api
        condition: log_ready                                  # Wait for ready_log_line
      - name: db
        condition: healthy                                    # Wait for health check

  db:
    command: postgres
    healthcheck:
      tcp_socket: "localhost:5432"                            # TCP probe (built-in)
      interval: 5s
      timeout: 3s

  cleanup:
    command: python scripts/cleanup.py
    schedule: "0 */6 * * *"                                   # Cron: every 6 hours

  db-migrate:
    command: alembic upgrade head
    context: docker
    container: ${DB_CONTAINER}                                # Docker execution

groups:
  backend:
    description: "Full backend stack"
    processes: [redis, db, api, worker]
    stop_order: [worker, api, db, redis]                      # Custom stop order

recipes:
  deploy:
    description: "Graceful deployment"
    on_error: stop
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

## CLI Reference

All commands return structured JSON. Run `procler capabilities` for the full machine-readable schema.

| Command | Description |
|---------|-------------|
| **Discovery** | |
| `procler capabilities` | JSON schema of all commands (LLM discovery) |
| `procler help-llm` | Comprehensive LLM usage guide |
| **Process Management** | |
| `procler define --name NAME --command CMD [opts]` | Define a process |
| `procler start NAME` | Start (idempotent) |
| `procler stop NAME` | Stop (idempotent) |
| `procler restart NAME [--clear-logs]` | Restart |
| `procler status [NAME]` | Status (all or single) |
| `procler list [--resolve] [--namespace NS]` | List definitions |
| `procler remove NAME` | Remove definition |
| `procler logs NAME [--tail N] [--since TIME] [-f]` | Logs |
| `procler exec "CMD" [--context TYPE] [--container NAME]` | One-off command |
| **Groups** | |
| `procler group list` | List groups |
| `procler group start\|stop\|status NAME` | Group operations |
| **Recipes** | |
| `procler recipe list` | List recipes |
| `procler recipe show NAME` | Recipe details |
| `procler recipe run NAME [--dry-run] [--continue-on-error]` | Execute recipe |
| **Snippets** | |
| `procler snippet list [--tag TAG]` | List snippets |
| `procler snippet show\|save\|run\|remove NAME` | Snippet CRUD |
| **Config** | |
| `procler config init [--force]` | Initialize .procler/ |
| `procler config validate` | Validate config |
| `procler config path` | Show config path |
| `procler config explain` | Plain-language explanation |
| **Export / Import** | |
| `procler export systemd NAME\|--all` | [C10] Export systemd units |
| `procler export compose` | [C11] Export docker-compose.yml |
| `procler import procfile PATH [--dry-run] [--merge]` | [C12] Import Procfile |
| **Other** | |
| `procler tui` | Terminal UI (requires `procler[tui]`) |
| `procler serve [--host H] [--port P] [--reload]` | Web server |

### Define Options

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
| `--daemon-container` | Container name for daemon detection |
| `--adopt-existing` | Adopt existing daemon if running (requires `--daemon-mode`) |
| `--force` | Overwrite existing definition |

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
| `/api/logs/{name}` | GET | Get logs (`?tail=100&since=5m`) |
| `/api/groups` | GET | List groups |
| `/api/groups/{name}/start` | POST | Start group |
| `/api/groups/{name}/stop` | POST | Stop group |
| `/api/groups/{name}/status` | GET | Group status |
| `/api/recipes` | GET | List recipes |
| `/api/recipes/{name}` | GET | Get recipe details |
| `/api/recipes/{name}/run` | POST | Run recipe |
| `/api/recipes/{name}/dry-run` | POST | Dry-run recipe |
| `/api/snippets` | GET | List snippets (`?tag=filter`) |
| `/api/snippets` | POST | Create snippet |
| `/api/snippets/{name}` | GET | Get snippet |
| `/api/snippets/{name}` | DELETE | Remove snippet |
| `/api/snippets/{name}/run` | POST | Run snippet |
| `/api/config` | GET | Config status |
| `/api/config/processes` | GET | Config process definitions |
| `/api/config/reload` | POST | Reload config |
| `/api/config/changelog` | GET | Changelog entries |
| `/api/config/export/{format}` | GET | Export (systemd, compose) |
| `/api/config/explain` | GET | Plain-language config explanation |
| `/api/health` | GET | Health check |
| `/api/ws` | WS | Real-time updates |

## Web Dashboard

Vue 3 frontend with Cyberpunk design. Start with `procler serve` and open http://localhost:8000.

- **Dashboard** — Process overview with real-time status
- **Process Detail** — Live log streaming via WebSocket, search/filter
- **Groups** — Card-based view, one-click start/stop all
- **Recipes** — Step preview, dry-run, execution progress
- **Snippets** — Save, manage, run reusable commands
- **Config** — Stats, variables, changelog viewer

Keyboard shortcuts: press `?` for all. Quick nav: `g d` dashboard, `g p` processes, `g g` groups, `g r` recipes, `g s` snippets.

> **Frontend dev:** `cd frontend && npm run dev` (port 5173), rebuild with `bash scripts/build_frontend.sh`

## Honest Limitations

- **Single-machine only** — Procler manages processes on one host. For multi-machine, use Nomad or Docker Swarm.
- **SQLite state** — Runtime state is local SQLite. Not suitable for clustered deployments.
- **Local logs only** — Log capture is filesystem-based. No remote log sinks (Splunk, Datadog, etc.).
- **One config per project** — Use `$PROCLER_CONFIG_DIR` to manage multiple configs per project.
- **No Windows support** — Linux and macOS only (`/proc` integration for process state).

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PROCLER_LOG_LEVEL` | `INFO` | Log level (DEBUG, INFO, WARNING, ERROR) |
| `PROCLER_LOG_FILE` | - | Log file path (auto-rotates) |
| `PROCLER_CONFIG_DIR` | `.procler/` | Config directory override |
| `PROCLER_DB_PATH` | `.procler/state.db` | Database path |
| `PROCLER_CORS_ORIGINS` | `localhost` | Comma-separated allowed origins |
| `PROCLER_DEBUG` | - | Enable detailed error messages |

## Development

```bash
uv sync --all-extras        # Install all dependencies
uv run pytest -v            # Run tests (320+)
uv run procler serve --reload  # Dev server with hot reload
```

## License

MIT
