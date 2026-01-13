# Changelog

All notable changes to Procler will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- Fixed graceful shutdown loop when pressing Ctrl+C multiple times
- Fixed log rotation to use correct `cleanup_all_logs()` method
- Fixed process recovery query to use proper sqler API
- Fixed graceful shutdown to use `status()` instead of non-existent `list_processes()`

### Changed

- Frontend static files now bundled in repository for easier deployment
- Updated `.gitignore` to track `procler/static/` directory

### Added

- Test coverage for application lifespan startup/shutdown

## [0.1.0] - 2026-01-08

### Added

- **Process Management**
  - Define, start, stop, restart, remove processes via CLI
  - Local subprocess execution with process groups
  - Docker container execution via docker-py SDK
  - PID-based process verification across sessions
  - Idempotent operations (start running process = no-op)

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
  - Log retrieval endpoint
  - Health check endpoint
  - OpenAPI documentation at `/api/docs`

- **WebSocket Real-time**
  - Live log streaming subscription
  - Status change broadcasts
  - Connection management with automatic cleanup

- **Vue 3 Frontend**
  - Process list with start/stop/restart controls
  - Process detail view with live log streaming
  - Snippets management UI
  - Cyberpunk design system (Naive UI + custom theme)

- **CLI**
  - JSON-native output for all commands
  - `capabilities` command for LLM discovery
  - Rich error context with suggestions
  - Exit codes for scripting

- **Production Features**
  - Build script for Vue to static files
  - FastAPI serves frontend in production
  - CORS configuration via environment variable
  - Global exception handler

### Technical Details

- Python 3.12+ required
- SQLite via sqler for persistence
- FastAPI for REST API and WebSocket
- Click for CLI
- Vue 3 + Vite + Pinia + Naive UI for frontend

[0.1.0]: https://github.com/gabu-quest/procler/releases/tag/v0.1.0
