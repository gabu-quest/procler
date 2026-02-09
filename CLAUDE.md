# Claude Context: Procler

**LLM-first process manager for developers.**

---

## What This Is

Procler provides a unified interface for managing development processes across local shells and Docker containers. All CLI output is JSON-native for programmatic use.

**Discovery commands:**
- `procler capabilities` - Full command schema (use this to discover commands)
- `procler config explain` - Plain-language config explanation
- `procler help-llm` - Comprehensive LLM-focused usage guide

For full CLI reference, REST API docs, and user-facing documentation, see `README.md`.

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
│   │   ├── process_manager.py  # Central coordinator + Linux state detection
│   │   ├── context_base.py     # Abstract ExecutionContext
│   │   ├── context_local.py    # Subprocess implementation
│   │   ├── context_docker.py   # Docker SDK implementation
│   │   ├── snippets.py         # Snippet operations
│   │   ├── groups.py           # Group operations (ordered start/stop + dependencies)
│   │   ├── recipes.py          # Recipe executor (multi-step)
│   │   ├── health.py           # Health check monitoring (cmd, HTTP, TCP probes)
│   │   ├── events.py           # EventBus for real-time updates
│   │   ├── scheduler.py        # Cron/scheduled process execution
│   │   ├── export.py           # Export to systemd/Docker Compose
│   │   └── import_procfile.py  # Procfile format importer
│   ├── api/                    # FastAPI application
│   │   ├── app.py              # App factory
│   │   ├── deps.py             # Dependency injection
│   │   └── routes/
│   │       ├── processes.py    # Process CRUD & control
│   │       ├── groups.py       # Group operations
│   │       ├── recipes.py      # Recipe execution
│   │       ├── config.py       # Config management
│   │       ├── logs.py         # Log retrieval
│   │       ├── snippets.py     # Snippet CRUD & run
│   │       └── ws.py           # WebSocket real-time
│   └── tui/                    # Terminal UI (Textual, optional extra)
│       └── app.py              # TUI app with process list, log viewer
├── frontend/                   # Vue 3 dashboard (Naive UI, Cyberpunk theme)
│   └── src/                    # views/, stores/, composables/, components/
├── tests/                      # pytest tests (320+)
└── scripts/
    ├── build_frontend.sh       # Build Vue to procler/static/
    └── record-demos.sh         # Terminal demo recordings (asciinema + agg)
```

---

## Tech Stack

- **Backend:** Python 3.12+, FastAPI, Click CLI
- **Database:** SQLite via [sqler](https://pypi.org/project/sqler/) (JSON-first micro-ORM)
- **Config:** YAML with Pydantic validation
- **Frontend:** Vue 3, Vite, Pinia, Naive UI
- **TUI:** Textual (optional `procler[tui]` extra)
- **Docker:** docker-py SDK
- **Scheduling:** croniter
- **Real-time:** WebSockets (native FastAPI)

---

## Architecture

```
CLI (Click) ──┐
Web UI (Vue) ──┤── FastAPI /api/... ── ProcessManager ──┬── LocalContext (subprocess)
TUI (Textual) ┘                       + Groups          ├── DockerContext (docker SDK)
                                      + Recipes          └── sqler Database
                                      + Health
                                      + Scheduler
```

Key: ProcessManager is the single source of truth. All interfaces share it.

---

## Design Principles

1. **JSON-native CLI** - All commands return `{success, data?, error?, error_code?, suggestion?}`
2. **Idempotent operations** - `start` on running = no-op, `stop` on stopped = no-op
3. **Dual interface parity** - CLI and Web UI share the same core
4. **Context abstraction** - Local and Docker are pluggable ExecutionContexts
5. **Version-controllable config** - `.procler/config.yaml` is committed to git

---

## Configuration

Per-project `.procler/` directory. Discovery: `$PROCLER_CONFIG_DIR` > `.procler.env` > `.procler/` > git root > `~/.procler/`

Config supports: processes (with healthchecks, replicas, namespaces, schedules, memory thresholds), groups, recipes, snippets, and variable substitution (`vars:` + `${VAR}`).

See `procler/config/schema.py` for the Pydantic models, or run `procler config explain` for a plain-language description.

---

## Security Notes

- All shell commands use `shlex.quote()` for user inputs
- Path traversal validation on pidfile and log paths
- Docker container names validated against safe patterns
- `asyncio.Lock()` on concurrent process handle access
- Try/finally cleanup for subprocesses and streams

---

## Development

```bash
uv sync --all-extras          # Install
uv run pytest tests/ -v       # Run tests (320+)
uv run python -m procler serve --reload  # Dev server
```

---

## Working in This Repo

- All CLI output MUST be valid JSON
- Tests use pytest with pytest-asyncio (`asyncio_mode = "auto"`)
- Follow existing patterns in the codebase
- Use `uv` for all Python operations
- Run tests before committing
- Config changes go in `.procler/config.yaml`, not runtime DB
- Frontend is pre-built in `procler/static/` (rebuild with `scripts/build_frontend.sh`)
