# PROCGLER - Project Roadmap

## North Star

**A process manager where Claude Code is a first-class citizen.**

Procgler exists to give developers (and their AI coding assistants) a single pane of glass for managing the chaos of modern development environments - where processes span local shells, Docker containers, and various execution contexts.

---

## Purpose & Problem Statement

### The Pain
Developers running multiple services face daily friction:
- 8+ processes scattered across tmux windows and Docker containers
- Manual start/stop ceremonies in separate terminals
- Forgetting exact commands to restart services
- No unified view of what's running vs. crashed
- Log files scattered across locations
- Rebuild steps forgotten before restart
- Useful command snippets lost in shell history

### The Solution
Procgler provides:
1. **Web Dashboard** - Visual monitoring, log viewing, one-click control
2. **LLM-First CLI** - JSON-native commands designed for Claude Code integration

Both interfaces are equals, sharing the same core logic. The CLI is not an afterthought wrapper - it's a primary interface optimized for programmatic use.

---

## Core Design Principles

### 1. LLM-First CLI Design
- **JSON-native output** - All commands return structured JSON, never human-formatted tables
- **Self-documenting** - `--capabilities` returns full command schema for discovery
- **Idempotent operations** - Safe to retry; `start` on running process returns current state
- **Rich error context** - Errors include suggestions and available options

### 2. Dual Interface Parity
- CLI and Web UI share the same `ProcessManager` core
- No feature exists in one interface without the other
- Same data model, same business logic

### 3. Context Abstraction
- Execution contexts (local, docker, future: WSL) are pluggable
- Process definitions are context-aware but interface-agnostic

### 4. Minimal Dependencies
- SQLite via sqler (no heavy ORMs)
- Standard library where possible
- Docker SDK only for container operations

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11+, FastAPI |
| Database | SQLite via sqler (JSON-first micro-ORM) |
| Frontend | Vue 3, Vite, Pinia |
| CLI | Click |
| Docker | docker-py SDK |
| Real-time | WebSockets (native FastAPI) |
| Serving | FastAPI serves Vue static files |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        INTERFACES                           │
├─────────────────────────────┬───────────────────────────────┤
│     CLI (click)             │      Web UI (Vue 3)           │
│     JSON output             │      WebSocket real-time      │
└─────────────┬───────────────┴───────────────┬───────────────┘
              │                               │
              │         FastAPI               │
              │        /api/...               │
              └───────────────┬───────────────┘
                              │
              ┌───────────────▼───────────────┐
              │        ProcessManager         │
              │      (Core Business Logic)    │
              └───────────────┬───────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ LocalContext  │   │ DockerContext │   │ Future: WSL   │
│ (subprocess)  │   │ (docker SDK)  │   │               │
└───────────────┘   └───────────────┘   └───────────────┘
                              │
              ┌───────────────▼───────────────┐
              │      sqler Database           │
              │  (processes, logs, snippets)  │
              └───────────────────────────────┘
```

---

## Data Model

### processes
```sql
CREATE TABLE processes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,           -- CLI identifier (e.g., "auth-api")
    display_name TEXT,                   -- Human-friendly (e.g., "Auth API")
    command TEXT NOT NULL,               -- Command to execute
    context_type TEXT DEFAULT 'local',   -- "local" | "docker"
    container_name TEXT,                 -- For docker context
    cwd TEXT,                            -- Working directory
    env_json TEXT,                       -- JSON object of env vars
    auto_restart INTEGER DEFAULT 0,      -- Boolean: restart on crash
    restart_delay_seconds INTEGER DEFAULT 5,
    tags_json TEXT,                      -- JSON array of tags
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### process_state
```sql
CREATE TABLE process_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    process_id INTEGER UNIQUE NOT NULL,
    status TEXT DEFAULT 'stopped',       -- stopped|running|error|starting|stopping
    pid INTEGER,                         -- OS process ID
    started_at TEXT,
    exit_code INTEGER,
    error_message TEXT,
    FOREIGN KEY (process_id) REFERENCES processes(id)
);
```

### logs
```sql
CREATE TABLE logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    process_id INTEGER NOT NULL,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    stream TEXT DEFAULT 'stdout',        -- stdout|stderr
    line TEXT,
    FOREIGN KEY (process_id) REFERENCES processes(id)
);

CREATE INDEX idx_logs_process_timestamp ON logs(process_id, timestamp DESC);
```

### snippets
```sql
CREATE TABLE snippets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    command TEXT NOT NULL,
    description TEXT,
    context_type TEXT DEFAULT 'local',
    container_name TEXT,
    tags_json TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

---

## CLI Command Reference

All commands output JSON to stdout. Exit code 0 on success, non-zero on failure.

### Discovery
```bash
procgler capabilities          # Returns JSON schema of all commands
```

### Process Control
```bash
procgler status [NAME]         # All processes or specific one
procgler start <NAME>          # Start (idempotent - no-op if running)
procgler stop <NAME>           # Stop (idempotent - no-op if stopped)
procgler restart <NAME>        # Stop then start
```

### Process Definitions
```bash
procgler define \
  --name <NAME> \
  --command <CMD> \
  --context <local|docker> \
  --container <CONTAINER> \     # Required if context=docker
  --cwd <PATH> \
  --display-name <DISPLAY> \
  --tags <TAG1,TAG2>

procgler remove <NAME>
procgler list                   # List all definitions
```

### Logs
```bash
procgler logs <NAME> \
  --tail <N> \                  # Last N lines (default: 100)
  --since <DURATION>            # e.g., "5m", "1h", ISO timestamp
```

### Arbitrary Execution
```bash
procgler exec <COMMAND> \
  --context <local|docker> \
  --container <CONTAINER> \
  --cwd <PATH>
```

### Snippets
```bash
procgler snippet list [--tag TAG]
procgler snippet save \
  --name <NAME> \
  --command <CMD> \
  --description <DESC> \
  --context <local|docker> \
  --container <CONTAINER> \
  --tags <TAG1,TAG2>
procgler snippet run <NAME>
procgler snippet remove <NAME>
```

### Example JSON Output
```json
// procgler status
{
  "success": true,
  "data": {
    "processes": [
      {
        "id": 1,
        "name": "auth-api",
        "display_name": "Auth API",
        "command": "uvicorn auth.main:app --port 8001",
        "context_type": "local",
        "status": "running",
        "pid": 12345,
        "uptime_seconds": 3600
      }
    ]
  }
}

// procgler start auth-api (already running)
{
  "success": true,
  "data": {
    "status": "already_running",
    "process": { ... }
  }
}

// Error response
{
  "success": false,
  "error": "Container 'db-postgres' not found",
  "error_code": "container_not_found",
  "suggestion": "Run 'docker ps -a' to list available containers",
  "available_containers": ["web-nginx", "api-fastapi"]
}
```

---

## Project Structure

```
procgler/
├── pyproject.toml
├── README.md
├── procgler/
│   ├── __init__.py
│   ├── __main__.py              # python -m procgler entrypoint
│   ├── cli.py                   # Click CLI definitions
│   ├── config.py                # Settings, paths, defaults
│   ├── db.py                    # sqler setup and migrations
│   ├── models.py                # Dataclasses for type hints
│   │
│   ├── core/                    # Shared business logic
│   │   ├── __init__.py
│   │   ├── process_manager.py   # Central coordinator
│   │   ├── context_base.py      # Abstract ExecutionContext
│   │   ├── context_local.py     # Subprocess implementation
│   │   ├── context_docker.py    # Docker SDK implementation
│   │   ├── log_collector.py     # Async log capture
│   │   └── snippets.py          # Snippet operations
│   │
│   ├── api/                     # FastAPI application
│   │   ├── __init__.py
│   │   ├── app.py               # App factory
│   │   ├── deps.py              # Dependency injection
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── processes.py
│   │       ├── logs.py
│   │       ├── snippets.py
│   │       └── ws.py            # WebSocket handler
│   │
│   └── static/                  # Vue build output (gitignored)
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── router.js
│       ├── stores/
│       │   └── processes.js     # Pinia store
│       ├── composables/
│       │   ├── useWebSocket.js
│       │   └── useApi.js
│       ├── components/
│       │   ├── ProcessCard.vue
│       │   ├── ProcessForm.vue
│       │   ├── LogViewer.vue
│       │   ├── SnippetList.vue
│       │   └── StatusBadge.vue
│       └── views/
│           ├── Dashboard.vue
│           ├── ProcessDetail.vue
│           └── Snippets.vue
│
├── tests/
│   ├── conftest.py
│   ├── test_cli.py
│   ├── test_process_manager.py
│   ├── test_context_local.py
│   ├── test_context_docker.py
│   └── test_api.py
│
└── scripts/
    ├── build_frontend.sh
    └── dev.sh
```

---

## Implementation Phases

### Phase 1: Foundation
**Goal:** Project scaffolding and database layer

**Deliverables:**
- [ ] Initialize project with pyproject.toml
- [ ] Set up directory structure
- [ ] Implement db.py with sqler table creation
- [ ] Create models.py with dataclasses
- [ ] Basic config.py (db path, defaults)
- [ ] CLI skeleton with `procgler capabilities` command
- [ ] `procgler --version`

**Acceptance Criteria:**
```bash
python -m procgler capabilities
# Returns valid JSON schema

python -m procgler --version
# Returns version string
```

---

### Phase 2: Core Process Management (Local)
**Goal:** Start/stop/restart local processes with log capture

**Deliverables:**
- [ ] context_base.py with abstract ExecutionContext
- [ ] context_local.py using asyncio.subprocess
- [ ] process_manager.py coordinating operations
- [ ] log_collector.py capturing stdout/stderr to database
- [ ] CLI commands: define, remove, list, status, start, stop, restart

**Acceptance Criteria:**
```bash
# Define a process
procgler define --name test-server --command "python -m http.server 8888"
# {"success": true, "action": "created", "name": "test-server"}

# Start it
procgler start test-server
# {"success": true, "data": {"status": "started", "pid": 12345}}

# Check status
procgler status test-server
# {"success": true, "data": {"process": {"status": "running", ...}}}

# Stop it
procgler stop test-server
# {"success": true, "data": {"status": "stopped"}}
```

---

### Phase 3: Logs & Exec
**Goal:** Log retrieval and arbitrary command execution

**Deliverables:**
- [ ] CLI logs command with --tail and --since
- [ ] CLI exec command for local context
- [ ] Log rotation/cleanup (keep last N entries per process)

**Acceptance Criteria:**
```bash
procgler logs test-server --tail 50
# {"success": true, "logs": [...], "count": 50}

procgler exec "ls -la" --cwd /tmp
# {"success": true, "data": {"stdout": "...", "exit_code": 0}}
```

---

### Phase 4: Docker Context
**Goal:** Execute processes inside Docker containers

**Deliverables:**
- [ ] context_docker.py using docker-py SDK
- [ ] Container discovery and validation
- [ ] Update define to accept --context docker --container
- [ ] exec command with docker context

**Acceptance Criteria:**
```bash
procgler define \
  --name db-migrate \
  --command "alembic upgrade head" \
  --context docker \
  --container api-container
# {"success": true, ...}

procgler start db-migrate
# Executes inside container

procgler exec "pip list" --context docker --container api-container
# {"success": true, "data": {"stdout": "..."}}
```

---

### Phase 5: Snippets
**Goal:** Reusable command library

**Deliverables:**
- [ ] snippets.py core logic
- [ ] CLI snippet subcommands: list, save, run, remove
- [ ] Tag filtering

**Acceptance Criteria:**
```bash
procgler snippet save \
  --name rebuild-api \
  --command "docker compose build api" \
  --tags docker,build

procgler snippet list --tag docker
# {"success": true, "snippets": [...]}

procgler snippet run rebuild-api
# Executes command, returns result
```

---

### Phase 6: FastAPI Backend
**Goal:** REST API matching CLI functionality

**Deliverables:**
- [ ] app.py with FastAPI factory
- [ ] routes/processes.py - CRUD + control endpoints
- [ ] routes/logs.py - log retrieval
- [ ] routes/snippets.py - snippet CRUD
- [ ] deps.py for dependency injection
- [ ] Shared ProcessManager instance

**API Endpoints:**
```
GET    /api/processes           List all
GET    /api/processes/{name}    Get one
POST   /api/processes           Create/update definition
DELETE /api/processes/{name}    Remove
POST   /api/processes/{name}/start
POST   /api/processes/{name}/stop
POST   /api/processes/{name}/restart

GET    /api/logs/{name}?tail=100&since=5m

GET    /api/snippets
POST   /api/snippets
DELETE /api/snippets/{name}
POST   /api/snippets/{name}/run
```

**Acceptance Criteria:**
```bash
curl http://localhost:8000/api/processes | jq
# Same structure as CLI output

curl -X POST http://localhost:8000/api/processes/test-server/start
# {"success": true, ...}
```

---

### Phase 7: WebSocket Real-time
**Goal:** Live status updates and log streaming

**Deliverables:**
- [ ] routes/ws.py WebSocket handler
- [ ] ConnectionManager for subscriptions
- [ ] Hook log_collector to broadcast new entries
- [ ] Status change broadcasts

**Protocol:**
```json
// Client -> Server
{"action": "subscribe_logs", "process_id": 1}
{"action": "unsubscribe_logs", "process_id": 1}

// Server -> Client
{"type": "status", "process_id": 1, "data": {"status": "running"}}
{"type": "log", "process_id": 1, "data": {"timestamp": "...", "line": "..."}}
```

---

### Phase 8: Vue Frontend - Foundation
**Goal:** Basic Vue app with routing and state

**Deliverables:**
- [ ] Vite + Vue 3 project setup
- [ ] Vue Router configuration
- [ ] Pinia store for processes
- [ ] useApi composable for fetch wrapper
- [ ] useWebSocket composable
- [ ] Basic layout component

**Views:**
- Dashboard (/)
- Process Detail (/process/:name)
- Snippets (/snippets)

---

### Phase 9: Vue Frontend - Dashboard
**Goal:** Main process overview with controls

**Deliverables:**
- [ ] Dashboard.vue - grid of process cards
- [ ] ProcessCard.vue - status, controls, quick info
- [ ] StatusBadge.vue - color-coded status indicator
- [ ] Start/Stop/Restart buttons with loading states
- [ ] Real-time status updates via WebSocket

---

### Phase 10: Vue Frontend - Process Detail & Logs
**Goal:** Individual process view with live logs

**Deliverables:**
- [ ] ProcessDetail.vue - full process info
- [ ] LogViewer.vue - scrolling log display
- [ ] Log filtering by stream (stdout/stderr)
- [ ] Auto-scroll with pause on manual scroll
- [ ] WebSocket log subscription

---

### Phase 11: Vue Frontend - Process Form & Snippets
**Goal:** CRUD interfaces

**Deliverables:**
- [ ] ProcessForm.vue - create/edit process definitions
- [ ] Context type switching (local/docker fields)
- [ ] Tag input component
- [ ] Snippets.vue - snippet list view
- [ ] SnippetForm.vue - create/edit snippets
- [ ] Run snippet with output display

---

### Phase 12: Production Polish
**Goal:** Production-ready deployment

**Deliverables:**
- [ ] Build script: compile Vue, copy to static/
- [ ] FastAPI serves static files in production
- [ ] CORS configuration for dev vs prod
- [ ] Error handling improvements
- [ ] Loading states throughout UI
- [ ] procgler serve command to start server
- [ ] README with installation and usage
- [ ] Basic test coverage

**Final Commands:**
```bash
# Development
cd frontend && npm run dev    # Vite dev server
procgler serve --reload       # FastAPI with hot reload

# Production
./scripts/build_frontend.sh   # Build Vue to static/
procgler serve                # Serves everything
```

---

## Dependencies

### pyproject.toml
```toml
[project]
name = "procgler"
version = "0.1.0"
description = "LLM-first process manager for developers"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "click>=8.1.0",
    "docker>=7.0.0",
    "sqler>=0.1.0",
    "websockets>=12.0",
]

[project.scripts]
procgler = "procgler.cli:cli"

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "httpx>=0.26.0",
    "ruff>=0.2.0",
]
```

### frontend/package.json
```json
{
  "name": "procgler-frontend",
  "version": "0.1.0",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.4.0",
    "vue-router": "^4.2.0",
    "pinia": "^2.1.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.0",
    "vite": "^5.0.0"
  }
}
```

---

## Success Criteria

### MVP Complete When:
1. ✅ Can define processes via CLI with JSON output
2. ✅ Can start/stop/restart local processes
3. ✅ Can start/stop/restart processes in Docker containers
4. ✅ Can view logs via CLI (--tail, --since)
5. ✅ Can execute arbitrary commands in any context
6. ✅ Can save and run command snippets
7. ✅ Web dashboard shows all processes with live status
8. ✅ Web UI has start/stop/restart buttons
9. ✅ Web UI shows live log streaming
10. ✅ Claude Code can use CLI to manage all processes

### Claude Code Integration Test:
```
Human: "My auth-api seems slow, check its recent logs and restart it if there are errors"

Claude Code:
1. procgler logs auth-api --tail 100
2. [Analyzes JSON log output]
3. procgler restart auth-api
4. procgler status auth-api
5. Reports back to human
```

---

## Future Enhancements (Post-MVP)

- [ ] Auto-restart on crash with configurable delay
- [ ] Health checks (HTTP endpoint, process exit monitoring)
- [ ] Process groups and bulk operations
- [ ] Rebuild hooks (run command before restart)
- [ ] Import/export process definitions (JSON/YAML)
- [ ] WSL context support
- [ ] Process resource monitoring (CPU, memory)
- [ ] Notification webhooks
- [ ] Multi-user support with auth
