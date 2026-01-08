# Claude Context: Procgler

**LLM-first process manager for developers.**

---

## What This Is

Procgler provides a unified interface for managing development processes across local shells and Docker containers. It's designed with Claude Code as a first-class citizen - all CLI output is JSON-native for programmatic use.

---

## Project Structure

```
procgler/
├── pyproject.toml              # Project config & dependencies
├── procgler/
│   ├── __init__.py
│   ├── __main__.py             # python -m procgler entrypoint
│   ├── cli.py                  # Click CLI definitions
│   ├── config.py               # Settings, paths, defaults
│   ├── db.py                   # sqler setup and migrations
│   ├── models.py               # SQLerModel definitions
│   ├── core/                   # Shared business logic
│   │   ├── process_manager.py  # Central coordinator
│   │   ├── context_base.py     # Abstract ExecutionContext
│   │   ├── context_local.py    # Subprocess implementation
│   │   ├── context_docker.py   # Docker SDK implementation
│   │   ├── snippets.py         # Snippet operations
│   │   └── events.py           # EventBus for real-time updates
│   └── api/                    # FastAPI application
│       ├── app.py              # App factory
│       ├── deps.py             # Dependency injection
│       └── routes/
│           ├── processes.py    # Process CRUD & control
│           ├── logs.py         # Log retrieval
│           ├── snippets.py     # Snippet CRUD & run
│           └── ws.py           # WebSocket real-time
├── frontend/                   # Vue 3 dashboard (Phase 8+)
└── tests/                      # pytest tests (91 tests)
```

---

## Tech Stack

- **Backend:** Python 3.12+, FastAPI, Click CLI
- **Database:** SQLite via [sqler](https://pypi.org/project/sqler/) (JSON-first micro-ORM)
- **Frontend:** Vue 3, Vite, Pinia (Phase 8+)
- **Docker:** docker-py SDK for container operations
- **Real-time:** WebSockets (native FastAPI)

---

## Key Design Principles

1. **JSON-native CLI** - All commands return structured JSON, never human-formatted tables
2. **Idempotent operations** - Safe to retry; `start` on running process returns current state
3. **Dual interface parity** - CLI and Web UI share the same ProcessManager core
4. **Context abstraction** - Local and Docker execution are pluggable contexts

---

## CLI Commands

All commands output JSON. Exit code 0 on success, non-zero on failure.

### Process Management
```bash
# Define a process
procgler define --name <NAME> --command <CMD> [--context local|docker] [--container <CONTAINER>] [--cwd <PATH>] [--tags <TAG1,TAG2>]

# Control processes
procgler start <NAME>      # Start (idempotent - no-op if running)
procgler stop <NAME>       # Stop (idempotent - no-op if stopped)
procgler restart <NAME>    # Stop then start

# View processes
procgler status [NAME]     # All processes or specific one
procgler list              # List all definitions

# Remove a process
procgler remove <NAME>
```

### Logs & Execution
```bash
# Get logs
procgler logs <NAME> --tail 100 --since 5m

# Execute arbitrary command
procgler exec "ls -la" --cwd /tmp [--context docker --container <CONTAINER>]
```

### Snippets (Reusable Commands)
```bash
procgler snippet list [--tag TAG]
procgler snippet save --name <NAME> --command <CMD> [--description <DESC>] [--tags <TAGS>]
procgler snippet run <NAME>
procgler snippet remove <NAME>
```

### Server
```bash
procgler serve [--host 127.0.0.1] [--port 8000] [--reload]
```

---

## REST API

Base URL: `http://localhost:8000/api`

### Processes
```
GET    /api/processes              # List all
GET    /api/processes/{name}       # Get one
POST   /api/processes              # Create (JSON body)
DELETE /api/processes/{name}       # Remove
POST   /api/processes/{name}/start
POST   /api/processes/{name}/stop
POST   /api/processes/{name}/restart
```

### Logs
```
GET    /api/logs/{name}?tail=100&since=5m
```

### Snippets
```
GET    /api/snippets[?tag=TAG]     # List (optional filter)
POST   /api/snippets               # Create (JSON body)
GET    /api/snippets/{name}        # Get one
DELETE /api/snippets/{name}        # Remove
POST   /api/snippets/{name}/run    # Execute
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
{"action": "subscribe_status", "process_id": 1}   // specific process
{"action": "subscribe_status"}                     // all processes
{"action": "unsubscribe_status", "process_id": 1}
{"action": "ping"}
```

### Server -> Client
```json
{"type": "log", "process_id": 1, "data": {"timestamp": "...", "stream": "stdout", "line": "..."}}
{"type": "status", "process_id": 1, "data": {"status": "running", "pid": 12345}}
{"type": "subscribed", "action": "subscribe_logs", "process_id": 1}
{"type": "unsubscribed", "action": "unsubscribe_logs", "process_id": 1}
{"type": "pong"}
{"type": "error", "message": "..."}
```

---

## Development

```bash
# Install dependencies
uv sync --all-extras

# Run CLI
uv run python -m procgler --help

# Run tests (91 tests)
uv run pytest tests/ -v

# Run dev server
uv run python -m procgler serve --reload
```

---

## Implementation Status

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Foundation (project setup, db, models) | ✅ |
| 2 | Core Process Management (start/stop/restart) | ✅ |
| 3 | Logs & Exec | ✅ |
| 4 | Docker Context | ✅ |
| 5 | Snippets | ✅ |
| 6 | FastAPI Backend | ✅ |
| 7 | WebSocket Real-time | ✅ |
| 8-11 | Vue Frontend | 🔲 |
| 12 | Production Polish | 🔲 |
| 13 | PyPI Publishing | 🔲 |

---

## Working in This Repo

- All CLI output MUST be valid JSON
- Tests use pytest with pytest-asyncio
- Follow existing patterns in the codebase
- Keep the repo healthy - incremental commits, tests alongside changes
- Use `uv` for dependency management
- Run tests before committing: `uv run pytest tests/ -v`

---

## Roadmap Reference

See `procgler-roadmap.md` for the full implementation plan with phases and acceptance criteria.
