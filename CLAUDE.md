# Claude Context: Procler

**LLM-first process manager for developers.**

---

## What This Is

Procler provides a unified interface for managing development processes across local shells and Docker containers. It's designed with Claude Code as a first-class citizen - all CLI output is JSON-native for programmatic use.

**Key LLM-friendly features:**
- All output is structured JSON with consistent `{success, data?, error?, error_code?, suggestion?}` format
- `procler capabilities` returns full command schema for discovery
- `procler config explain` describes config in plain language
- Per-project version-controllable configuration

---

## Quick Start for Claude

```bash
# Discover all commands
procler capabilities

# Understand current config
procler config explain

# Common workflows
procler group start backend     # Start dev environment
procler recipe run deploy       # Execute multi-step operation
procler status                  # Check all processes
```

---

## Project Structure

```
procler/
├── pyproject.toml              # Project config & dependencies
├── procler/
│   ├── __init__.py
│   ├── __main__.py             # python -m procler entrypoint
│   ├── cli.py                  # Click CLI definitions
│   ├── settings.py             # Settings, paths, defaults
│   ├── db.py                   # sqler setup and migrations
│   ├── models.py               # SQLerModel definitions
│   ├── config/                 # YAML config system
│   │   ├── schema.py           # Pydantic models for config
│   │   ├── loader.py           # Config discovery and loading
│   │   └── changelog.py        # Append-only audit trail
│   ├── core/                   # Shared business logic
│   │   ├── process_manager.py  # Central coordinator
│   │   ├── context_base.py     # Abstract ExecutionContext
│   │   ├── context_local.py    # Subprocess implementation
│   │   ├── context_docker.py   # Docker SDK implementation
│   │   ├── snippets.py         # Snippet operations
│   │   ├── groups.py           # Group operations (ordered start/stop)
│   │   ├── recipes.py          # Recipe executor (multi-step)
│   │   └── events.py           # EventBus for real-time updates
│   └── api/                    # FastAPI application
│       ├── app.py              # App factory
│       ├── deps.py             # Dependency injection
│       └── routes/
│           ├── processes.py    # Process CRUD & control
│           ├── groups.py       # Group operations
│           ├── recipes.py      # Recipe execution
│           ├── config.py       # Config management
│           ├── logs.py         # Log retrieval
│           ├── snippets.py     # Snippet CRUD & run
│           └── ws.py           # WebSocket real-time
├── frontend/                   # Vue 3 dashboard
│   ├── src/
│   │   ├── views/              # Dashboard, Processes, Groups, Recipes, Snippets, Config
│   │   ├── stores/             # Pinia state management
│   │   └── ...
│   └── package.json
└── tests/                      # pytest tests (91 tests)
```

---

## Tech Stack

- **Backend:** Python 3.12+, FastAPI, Click CLI
- **Database:** SQLite via [sqler](https://pypi.org/project/sqler/) (JSON-first micro-ORM)
- **Config:** YAML with Pydantic validation
- **Frontend:** Vue 3, Vite, Pinia, Naive UI (Cyberpunk theme)
- **Docker:** docker-py SDK for container operations
- **Real-time:** WebSockets (native FastAPI)

---

## Key Design Principles

1. **JSON-native CLI** - All commands return structured JSON, never human-formatted tables
2. **Idempotent operations** - Safe to retry; `start` on running process returns current state
3. **Dual interface parity** - CLI and Web UI share the same ProcessManager core
4. **Context abstraction** - Local and Docker execution are pluggable contexts
5. **Version-controllable config** - `.procler/config.yaml` is committed to git
6. **Audit trail** - All operations logged to `.procler/changelog.log`

---

## Configuration System

Procler uses a per-project `.procler/` directory:

```
.procler/
├── config.yaml    # Definitions (commit to git)
├── changelog.log  # Audit trail (commit to git)
└── state.db       # Runtime state (auto-gitignored)
```

**Discovery order:** `$PROCLER_CONFIG_DIR` → `.procler.env` → `.procler/` → git root → `~/.procler/`

### Config Schema

```yaml
version: 1

processes:
  api:
    command: uvicorn main:app --reload
    context: local  # or docker
    container: my-container  # required if docker
    cwd: /path/to/project
    tags: [backend, api]
    description: "API server"

groups:
  backend:
    description: "Full backend stack"
    processes: [redis, api, worker]  # Start order
    stop_order: [worker, api, redis]  # Optional, defaults to reversed

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
        container: my-container
      - start: api
      - start: worker

snippets:
  rebuild:
    command: docker compose build
    description: "Rebuild containers"
    tags: [docker]
```

---

## CLI Commands

All commands output JSON. Exit code 0 on success, non-zero on failure.

### Discovery & Config
```bash
procler capabilities          # Full command schema (LLM discovery)
procler config init           # Create .procler/ with template
procler config validate       # Validate config.yaml
procler config explain        # Plain-language explanation
procler config path           # Show resolved paths
```

### Process Management
```bash
procler define --name <NAME> --command <CMD> [--context local|docker] [--container <CONTAINER>]
procler start <NAME>          # Idempotent
procler stop <NAME>           # Idempotent
procler restart <NAME>
procler status [NAME]
procler list
procler remove <NAME>
procler logs <NAME> --tail 100 --since 5m
procler exec "command" [--context docker --container <CONTAINER>]
```

### Groups (Ordered Start/Stop)
```bash
procler group list
procler group start <NAME>    # Start processes in order
procler group stop <NAME>     # Stop in reverse order
procler group status <NAME>
```

### Recipes (Multi-Step Operations)
```bash
procler recipe list
procler recipe show <NAME>
procler recipe run <NAME> --dry-run     # Preview
procler recipe run <NAME>               # Execute
procler recipe run <NAME> --continue-on-error
```

### Snippets
```bash
procler snippet list [--tag TAG]
procler snippet save --name <NAME> --command <CMD>
procler snippet run <NAME>
procler snippet remove <NAME>
```

### Server
```bash
procler serve [--host 127.0.0.1] [--port 8000] [--reload]
```

---

## REST API

Base URL: `http://localhost:8000/api`

### Processes
```
GET    /api/processes              # List all
GET    /api/processes/{name}       # Get one
POST   /api/processes              # Create
DELETE /api/processes/{name}       # Remove
POST   /api/processes/{name}/start
POST   /api/processes/{name}/stop
POST   /api/processes/{name}/restart
GET    /api/logs/{name}?tail=100&since=5m
```

### Groups
```
GET    /api/groups                 # List all
GET    /api/groups/{name}          # Get one
GET    /api/groups/{name}/status   # Status of all processes
POST   /api/groups/{name}/start    # Start in order
POST   /api/groups/{name}/stop     # Stop in reverse order
```

### Recipes
```
GET    /api/recipes                # List all
GET    /api/recipes/{name}         # Get details
POST   /api/recipes/{name}/run     # Execute (body: {dry_run?, continue_on_error?})
POST   /api/recipes/{name}/dry-run # Preview only
```

### Config
```
GET    /api/config                 # Status and stats
GET    /api/config/processes       # List config-defined processes
GET    /api/config/changelog?format=parsed&tail=50
GET    /api/config/explain         # Plain-language explanation
POST   /api/config/reload          # Reload from disk
```

### Snippets
```
GET    /api/snippets[?tag=TAG]
POST   /api/snippets
GET    /api/snippets/{name}
DELETE /api/snippets/{name}
POST   /api/snippets/{name}/run
```

### Health
```
GET    /api/health                 # {"status": "healthy", "version": "..."}
```

---

## WebSocket Protocol

Connect to `ws://localhost:8000/api/ws`

### Client -> Server
```json
{"action": "subscribe_logs", "process_id": 1}
{"action": "unsubscribe_logs", "process_id": 1}
{"action": "subscribe_status", "process_id": 1}
{"action": "subscribe_status"}  // all processes
{"action": "unsubscribe_status", "process_id": 1}
{"action": "ping"}
```

### Server -> Client
```json
{"type": "log", "process_id": 1, "data": {"timestamp": "...", "stream": "stdout", "line": "..."}}
{"type": "status", "process_id": 1, "data": {"status": "running", "pid": 12345}}
{"type": "subscribed", "action": "subscribe_logs", "process_id": 1}
{"type": "pong"}
{"type": "error", "message": "..."}
```

---

## Frontend

The Vue 3 dashboard provides:

| View | Purpose |
|------|---------|
| Dashboard | Overview with stats, quick actions, recent activity |
| Processes | Process list with CRUD, status indicators |
| Process Detail | Live logs, controls |
| Groups | Card-based view, one-click start/stop all |
| Recipes | Step preview, dry-run, execution progress |
| Snippets | Reusable command management |
| Config | Status, stats, changelog viewer |

### Running Frontend

```bash
cd frontend
npm install
npm run dev      # Development at :5173 (proxies /api to :8000)
npm run build    # Production build
```

### Production

```bash
./scripts/build_frontend.sh      # Build to procler/static/
procler serve --host 0.0.0.0     # Serves both API and frontend
```

Environment variables:
- `PROCLER_CORS_ORIGINS` - Comma-separated allowed origins
- `PROCLER_DEBUG` - Show detailed errors

---

## Development

```bash
# Install
uv sync --all-extras

# Run CLI
uv run python -m procler --help

# Run tests (91 tests)
uv run pytest tests/ -v

# Dev server
uv run python -m procler serve --reload
```

---

## Working in This Repo

- All CLI output MUST be valid JSON
- Tests use pytest with pytest-asyncio
- Follow existing patterns in the codebase
- Keep the repo healthy - incremental commits, tests alongside changes
- Use `uv` for dependency management
- Run tests before committing: `uv run pytest tests/ -v`
- Config changes should be in `.procler/config.yaml`, not runtime DB

---

## Common Workflows

### Start a dev environment
```bash
procler group start backend
procler status
```

### Debug a failing process
```bash
procler status api
procler logs api --tail 50
procler restart api
```

### Graceful deployment
```bash
procler recipe run deploy --dry-run  # Preview
procler recipe run deploy            # Execute
```

### Initialize new project
```bash
procler config init
# Edit .procler/config.yaml
procler config validate
procler config explain
```
