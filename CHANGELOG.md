# Changelog

All notable changes to Procler will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Health Check Probes**
  - HTTP GET probe (`http_get:`) - built-in, no curl needed
  - TCP socket probe (`tcp_socket:`) - built-in connectivity check
  - Command probe (`test:`) - run arbitrary health check commands
  - Configurable interval, timeout, retries, and start period

- **Dependency Conditions**
  - `log_ready` condition - wait for a regex match in process stdout (`ready_log_line:`)
  - `healthy` condition - wait for health check to pass
  - `started` condition (default) - wait for process to be running

- **Memory Threshold Restart**
  - `max_memory:` config option (supports K, M, G suffixes)
  - Auto-restart when process RSS exceeds threshold

- **Process Replicas**
  - `replicas: N` config option creates N instances (e.g., worker-1, worker-2, worker-3)
  - Each replica gets `PROCLER_REPLICA_INDEX` environment variable

- **Namespace Isolation**
  - `namespace:` config option for grouping processes (default: "default")
  - `procler list --namespace NS` to filter by namespace

- **Cron/Scheduled Processes**
  - `schedule:` config option with cron expression (e.g., `"0 */6 * * *"`)
  - Scheduler runs processes on schedule via croniter

- **Export**
  - `procler export systemd NAME` - export as systemd .service unit file
  - `procler export systemd --all` - export all local processes
  - `procler export compose` - export as docker-compose.yml
  - `GET /api/config/export/{format}` API endpoint

- **Import**
  - `procler import procfile PATH` - import processes from Procfile (Foreman/Overmind)
  - `--dry-run` to preview without writing
  - `--merge` to merge into existing config

- **Terminal UI (TUI)**
  - `procler tui` - interactive terminal UI powered by Textual
  - Process list with status indicators
  - Live log viewer
  - Start/stop/restart controls
  - Available as optional extra: `pip install procler[tui]`

- **Demo Recording**
  - `scripts/record-demos.sh` for generating terminal demo recordings
  - Supports asciinema (.cast), SVG, and GIF output formats

### Fixed

- Fixed graceful shutdown loop when pressing Ctrl+C multiple times
- Fixed log rotation to use correct `cleanup_all_logs()` method
- Fixed process recovery query to use proper sqler API
- Fixed graceful shutdown to use `status()` instead of non-existent `list_processes()`

### Changed

- Frontend static files now bundled in repository for easier deployment
- Updated `.gitignore` to track `procler/static/` directory
- Test suite expanded from 154 to 320+ tests

## [0.1.0] - 2026-01-08

### Added

- **Process Management**
  - Define, start, stop, restart, remove processes via CLI
  - Local subprocess execution with process groups
  - Docker container execution via docker-py SDK
  - PID-based process verification across sessions
  - Idempotent operations (start running process = no-op)

- **Configuration System**
  - YAML config with Pydantic validation
  - Per-project `.procler/` directory with discovery order
  - Config variables (`vars:` with `${VAR}` substitution)
  - `procler config init/validate/explain/path` commands
  - Append-only audit trail in `changelog.log`

- **Groups & Recipes**
  - Groups with ordered start/stop and dependency resolution
  - Recipes for multi-step operations with dry-run support
  - `on_error: stop|continue` for recipe error handling

- **Logging**
  - Automatic stdout/stderr capture to SQLite
  - Log retrieval with `--tail` and `--since` filters
  - Log rotation and cleanup per process

- **Snippets**
  - Save reusable commands with descriptions and tags
  - Tag filtering for snippet organization
  - Execute snippets in local or Docker context

- **REST API**
  - Full CRUD operations for processes and snippets
  - Group and recipe endpoints
  - Log retrieval endpoint
  - Health check endpoint
  - OpenAPI documentation at `/api/docs`

- **WebSocket Real-time**
  - Live log streaming subscription
  - Status change broadcasts
  - Connection management with automatic cleanup

- **Vue 3 Frontend**
  - Dashboard with stats, quick actions, recent activity
  - Process list with start/stop/restart controls
  - Process detail view with live log streaming and search/filter
  - Groups card-based view with one-click start/stop
  - Recipes step preview, dry-run, execution progress
  - Snippets management with confirmations
  - Config status, stats, changelog viewer
  - Cyberpunk design system (Naive UI + custom theme)
  - Keyboard shortcuts (`?` to view all)
  - WebSocket connection status indicator
  - Toast notifications for process status changes

- **CLI**
  - JSON-native output for all commands
  - `capabilities` command for LLM discovery
  - `help-llm` command for comprehensive LLM-focused usage guide
  - Rich error context with suggestions
  - Exit codes for scripting

- **Production Features**
  - Build script for Vue to static files
  - FastAPI serves frontend in production
  - CORS configuration via environment variable
  - Process recovery on startup
  - Graceful shutdown with SIGTERM/SIGINT
  - Auto log rotation (configurable interval)
  - Structured logging with loguru
  - Database schema versioning with automatic migrations

- **Security**
  - Command injection prevention with `shlex.quote()`
  - Path traversal validation for pidfile and log paths
  - Docker container name validation
  - Thread-safe process handles with `asyncio.Lock()`
  - Resource cleanup with try/finally patterns
  - Stream reader timeout protection

### Technical Details

- Python 3.12+ required
- SQLite via sqler for persistence
- FastAPI for REST API and WebSocket
- Click for CLI
- Vue 3 + Vite + Pinia + Naive UI for frontend

[Unreleased]: https://github.com/gabu-quest/procler/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/gabu-quest/procler/releases/tag/v0.1.0
