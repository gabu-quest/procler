# PROCLER - Project Roadmap

## North Star

**A process manager where Claude Code is a first-class citizen.**

Procler exists to give developers (and their AI coding assistants) a single pane of glass for managing the chaos of modern development environments - where processes span local shells, Docker containers, and various execution contexts.

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
Procler provides:
1. **Web Dashboard** - Visual monitoring, log viewing, one-click control
2. **LLM-First CLI** - JSON-native commands designed for Claude Code integration
3. **Terminal UI** - Interactive TUI for terminal-native workflows

All interfaces share the same core logic. The CLI is not an afterthought wrapper - it's a primary interface optimized for programmatic use.

---

## Core Design Principles

### 1. LLM-First CLI Design
- **JSON-native output** - All commands return structured JSON, never human-formatted tables
- **Self-documenting** - `capabilities` returns full command schema for discovery
- **Idempotent operations** - Safe to retry; `start` on running process returns current state
- **Rich error context** - Errors include suggestions and available options

### 2. Dual Interface Parity
- CLI and Web UI share the same `ProcessManager` core
- No feature exists in one interface without the other
- Same data model, same business logic

### 3. Context Abstraction
- Execution contexts (local, docker) are pluggable
- Process definitions are context-aware but interface-agnostic

### 4. Minimal Dependencies
- SQLite via sqler (no heavy ORMs)
- Standard library where possible
- Docker SDK only for container operations

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.12+, FastAPI |
| Database | SQLite via sqler (JSON-first micro-ORM) |
| Config | YAML with Pydantic validation |
| Frontend | Vue 3, Vite, Pinia, Naive UI |
| CLI | Click |
| TUI | Textual (optional extra) |
| Docker | docker-py SDK |
| Real-time | WebSockets (native FastAPI) |
| Scheduling | croniter |
| Serving | FastAPI serves Vue static files |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        INTERFACES                           │
├──────────────┬────────────────────┬─────────────────────────┤
│  CLI (click) │   Web UI (Vue 3)   │   TUI (Textual)        │
│  JSON output │   WebSocket        │   Interactive terminal  │
└──────┬───────┴──────────┬─────────┴───────────┬─────────────┘
       │                  │                     │
       │           FastAPI /api/...             │
       └──────────────────┬─────────────────────┘
                          │
           ┌──────────────▼──────────────┐
           │      ProcessManager         │
           │   (Core Business Logic)     │
           │   + Groups, Recipes,        │
           │     Health, Scheduler       │
           └──────────────┬──────────────┘
                          │
       ┌──────────────────┼──────────────────┐
       │                  │                  │
       ▼                  ▼                  ▼
┌─────────────┐  ┌──────────────┐  ┌──────────────┐
│ LocalContext │  │ DockerContext │  │ Future: WSL  │
│ (subprocess) │  │ (docker SDK) │  │              │
└─────────────┘  └──────────────┘  └──────────────┘
                          │
           ┌──────────────▼──────────────┐
           │      sqler Database         │
           │ (processes, logs, snippets) │
           └─────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Foundation ✅
**Goal:** Project scaffolding and database layer

- [x] Initialize project with pyproject.toml
- [x] Set up directory structure
- [x] Implement db.py with sqler table creation
- [x] Create models.py with dataclasses
- [x] Basic config.py (db path, defaults)
- [x] CLI skeleton with `procler capabilities` command
- [x] `procler --version`

---

### Phase 2: Core Process Management (Local) ✅
**Goal:** Start/stop/restart local processes with log capture

- [x] context_base.py with abstract ExecutionContext
- [x] context_local.py using asyncio.subprocess
- [x] process_manager.py coordinating operations
- [x] Log capture of stdout/stderr to database
- [x] CLI commands: define, remove, list, status, start, stop, restart

---

### Phase 3: Logs & Exec ✅
**Goal:** Log retrieval and arbitrary command execution

- [x] CLI logs command with --tail and --since
- [x] CLI exec command for local context
- [x] Log rotation/cleanup (keep last N entries per process)

---

### Phase 4: Docker Context ✅
**Goal:** Execute processes inside Docker containers

- [x] context_docker.py using docker-py SDK
- [x] Container discovery and validation
- [x] Update define to accept --context docker --container
- [x] exec command with docker context

---

### Phase 5: Snippets ✅
**Goal:** Reusable command library

- [x] snippets.py core logic
- [x] CLI snippet subcommands: list, save, run, remove
- [x] Tag filtering

---

### Phase 6: FastAPI Backend ✅
**Goal:** REST API matching CLI functionality

- [x] app.py with FastAPI factory
- [x] routes/processes.py - CRUD + control endpoints
- [x] routes/logs.py - log retrieval
- [x] routes/snippets.py - snippet CRUD
- [x] deps.py for dependency injection
- [x] Shared ProcessManager instance

---

### Phase 7: WebSocket Real-time ✅
**Goal:** Live status updates and log streaming

- [x] routes/ws.py WebSocket handler
- [x] ConnectionManager for subscriptions
- [x] Hook log capture to broadcast new entries
- [x] Status change broadcasts

---

### Phase 8: Vue Frontend - Foundation ✅
**Goal:** Basic Vue app with routing and state

- [x] Vite + Vue 3 project setup
- [x] Vue Router configuration
- [x] Pinia store for processes
- [x] useApi composable for fetch wrapper
- [x] useWebSocket composable
- [x] Basic layout component (AppLayout with Cyberpunk theme)

---

### Phase 9: Vue Frontend - Dashboard ✅
**Goal:** Main process overview with controls

- [x] Dashboard.vue - stats, quick actions, recent activity
- [x] Process list with status indicators
- [x] Start/Stop/Restart buttons with per-action loading states
- [x] Real-time status updates via WebSocket

---

### Phase 10: Vue Frontend - Process Detail & Logs ✅
**Goal:** Individual process view with live logs

- [x] ProcessDetail.vue - full process info with breadcrumbs
- [x] LogViewer with scrolling log display
- [x] Log filtering by text (with match highlighting)
- [x] Log filtering by stream (stdout/stderr)
- [x] WebSocket log subscription

---

### Phase 11: Vue Frontend - Groups, Recipes, Snippets ✅
**Goal:** Full feature coverage in web UI

- [x] Groups card-based view with one-click start/stop
- [x] Recipes step preview, dry-run, execution progress
- [x] Snippets management with confirmations
- [x] Config view with stats, variables, changelog
- [x] Keyboard shortcuts (press `?` to view all)

---

### Phase 12: Production Polish ✅
**Goal:** Production-ready deployment

- [x] Build script: compile Vue, copy to static/
- [x] FastAPI serves static files in production
- [x] CORS configuration for dev vs prod
- [x] Error handling improvements
- [x] Loading states throughout UI
- [x] procler serve command to start server
- [x] README with installation and usage
- [x] 320+ tests

---

### Phase 13: PyPI Publishing ✅
**Goal:** Package and publish to PyPI for easy installation

- [x] Finalize pyproject.toml metadata (author, classifiers, URLs)
- [x] Add project URLs (homepage, repository, documentation)
- [x] Create CHANGELOG.md with release notes
- [x] Set up GitHub Actions for automated publishing
- [x] Configure trusted publishing with PyPI
- [x] Publish initial release to PyPI
- [x] Verify `pip install procler` works

---

### Phase 14: YAML Config System ✅
**Goal:** Version-controllable project configuration

- [x] Pydantic models for config schema
- [x] YAML config loader with discovery order
- [x] Config variables (`vars:` with `${VAR}` substitution)
- [x] Config init, validate, explain, path commands
- [x] Append-only audit trail (changelog.log)

---

### Phase 15: Groups & Recipes ✅
**Goal:** Orchestrated multi-process workflows

- [x] Groups with ordered start/stop and dependency resolution
- [x] Recipes for multi-step operations
- [x] Dry-run support for recipes
- [x] on_error: stop|continue for recipe error handling

---

### Phase 16: Health Checks & Dependencies ✅
**Goal:** Process health monitoring and smart dependency resolution

- [x] Command probe (`test:`)
- [x] HTTP GET probe (`http_get:`) - built-in, no curl needed
- [x] TCP socket probe (`tcp_socket:`) - built-in connectivity check
- [x] `log_ready` dependency condition (regex match on stdout)
- [x] `healthy` dependency condition (health check pass)
- [x] Configurable interval, timeout, retries, start_period

---

### Phase 17: Advanced Process Features ✅
**Goal:** Production-grade process management

- [x] Memory threshold restart (`max_memory:`)
- [x] Process replicas (`replicas: N`)
- [x] Namespace isolation (`namespace:`)
- [x] Cron/scheduled execution (`schedule:`)

---

### Phase 18: Export & Import ✅
**Goal:** Interoperability with other tools

- [x] Export to systemd .service unit files
- [x] Export to docker-compose.yml
- [x] Import from Procfile (Foreman/Overmind migration)
- [x] Dry-run and merge modes for import

---

### Phase 19: Terminal UI ✅
**Goal:** Interactive terminal interface

- [x] Textual-based TUI with process list
- [x] Live log viewer
- [x] Start/stop/restart controls
- [x] Optional extra: `procler[tui]`

---

## Success Criteria

### MVP Complete ✅
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

### Beyond MVP ✅
11. ✅ Health checks with HTTP/TCP/command probes
12. ✅ Groups with dependency-ordered startup
13. ✅ Recipes for multi-step operations
14. ✅ Process replicas and namespace isolation
15. ✅ Cron/scheduled execution
16. ✅ Export to systemd and Docker Compose
17. ✅ Import from Procfile
18. ✅ Terminal UI (TUI)
19. ✅ 320+ tests

---

## Future Enhancements

- [ ] WSL context support
- [ ] Notification webhooks (Slack, Discord)
- [ ] Multi-user support with auth
- [ ] Process CPU/memory monitoring dashboard
- [ ] Auto-restart on crash with configurable delay and backoff
- [ ] Rebuild hooks (run command before restart)
- [ ] Remote agent mode (manage processes on remote hosts)
- [ ] Plugin system for custom contexts
