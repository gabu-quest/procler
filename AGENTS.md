# Procler - Agent Usage Guide

This document provides comprehensive instructions for LLM agents to use Procler, an LLM-first process manager.

---

## Quick Reference

```bash
# Discovery
procler capabilities       # JSON schema of all commands
procler help-llm          # Comprehensive usage guide (JSON with markdown)
procler config explain    # Plain-language config explanation

# Process Management
procler start <name>      # Idempotent
procler stop <name>       # Idempotent
procler restart <name>    # With optional --clear-logs
procler status [name]     # Status with Linux kernel state
procler logs <name>       # --tail N, --since 5m
procler list              # --namespace NS to filter

# Groups & Recipes
procler group start <name>    # Ordered startup with dependencies
procler recipe run <name>     # Multi-step operation (--dry-run to preview)

# Export & Import
procler export systemd <name>     # Export as systemd unit
procler export compose            # Export as docker-compose.yml
procler import procfile <path>    # Import from Procfile

# TUI
procler tui                       # Interactive terminal UI
```

---

## Response Format

All CLI commands return JSON to stdout. Parse the response as follows:

### Success
```json
{
  "success": true,
  "data": {
    "process": { "name": "api", "status": "running", "pid": 12345 }
  }
}
```

### Error
```json
{
  "success": false,
  "error": "Process 'api' not found",
  "error_code": "process_not_found",
  "suggestion": "Run 'procler list' to see available processes"
}
```

**Always check `success` field first.** Use `error_code` for programmatic error handling and `suggestion` for recovery actions.

---

## CLI Help

```
Usage: procler [OPTIONS] COMMAND [ARGS]...

  Procler - LLM-first process manager for developers.
  All commands output JSON for easy parsing by scripts and LLMs.

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  capabilities  Returns JSON schema of all commands.
  config        Manage configuration (config.yaml).
  define        Define a new process.
  exec          Execute an arbitrary command.
  export        Export processes (systemd, docker-compose).
  group         Manage process groups (defined in config.yaml).
  help-llm      Output comprehensive LLM-focused usage instructions.
  import        Import processes from external formats.
  list          List all process definitions.
  logs          Get logs for a process.
  recipe        Manage and run recipes (multi-step operations).
  remove        Remove a process definition.
  restart       Restart a process (stop then start).
  serve         Start the web server.
  snippet       Manage command snippets.
  start         Start a process (idempotent - no-op if running).
  status        Show status of all processes or a specific one.
  stop          Stop a process (idempotent - no-op if stopped).
  tui           Launch interactive Terminal UI.
```

---

## Command Discovery

Run `procler capabilities` to get a complete JSON schema of all available commands, their arguments, options, and examples. This is the recommended way for agents to discover functionality.

Run `procler help-llm` for a markdown-formatted comprehensive guide embedded in JSON.

---

## Process Management

### Define a Process
```bash
procler define --name api --command 'uvicorn main:app' --cwd /app
procler define --name worker --command 'celery worker' --context docker --container myapp
```

### Start/Stop/Restart
```bash
procler start api      # Returns immediately, process runs in background
procler stop api       # Sends SIGTERM, waits for graceful shutdown
procler restart api    # Stop then start
procler restart api --clear-logs  # Clear accumulated logs
```

**Idempotency**: `start` on a running process and `stop` on a stopped process are no-ops that return success.

### Status
```bash
procler status         # All processes
procler status api     # Specific process
```

Response includes:
- `status`: "running" | "stopped" | "failed"
- `pid`: Process ID (null if not running)
- `uptime_seconds`: Time since start
- `linux_state`: Kernel state information
- `warning`: Alert for problematic states (D, Z)

### Linux Process States
| Code | Name | Description | Killable |
|------|------|-------------|----------|
| R | running | On run queue | Yes |
| S | sleeping | Interruptible sleep | Yes |
| D | disk_sleep | Uninterruptible (I/O wait) | **No** |
| Z | zombie | Terminated, not reaped | **No** |
| T | stopped | Job control signal | Yes |

**Important**: Processes in D state cannot be killed. Wait for I/O to complete.

### Logs
```bash
procler logs api                    # Last 100 lines
procler logs api --tail 50          # Last 50 lines
procler logs api --since 5m         # Last 5 minutes
procler logs api --since 1h         # Last hour
```

### List with Namespace Filter
```bash
procler list                        # All processes
procler list --namespace backend    # Filter by namespace
```

---

## Groups

Groups define ordered startup sequences with optional dependencies.

```bash
procler group list                  # List all groups
procler group start backend         # Start processes in order
procler group stop backend          # Stop in reverse order
procler group status backend        # Status of all group processes
```

### Config Example
```yaml
groups:
  backend:
    processes: [redis, database, api, worker]
    stop_order: [worker, api, database, redis]  # Optional custom order
```

### Dependencies
```yaml
processes:
  api:
    command: uvicorn main:app
    ready_log_line: "Uvicorn running on"  # Regex for log_ready
    depends_on:
      - redis                    # Wait for 'started'
      - name: database
        condition: healthy       # Wait for health check pass
      - name: cache
        condition: log_ready     # Wait for ready_log_line match
```

---

## Recipes

Recipes are multi-step automation workflows.

```bash
procler recipe list
procler recipe show deploy          # View steps
procler recipe run deploy --dry-run # Preview without executing
procler recipe run deploy           # Execute
procler recipe run deploy --continue-on-error
```

### Config Example
```yaml
recipes:
  deploy:
    description: "Graceful deployment with migration"
    on_error: stop  # or continue
    steps:
      - stop: worker
      - stop: api
      - wait: 2s
      - exec: "alembic upgrade head"
        context: docker
        container: myapp
      - start: api
      - start: worker
```

### Step Types
- `start: <process>` - Start a process
- `stop: <process>` - Stop a process
- `restart: <process>` - Restart a process
- `exec: "<command>"` - Run a one-off command
- `wait: <duration>` - Pause (e.g., "5s", "1m")

---

## Snippets

Snippets are saved commands for quick execution.

```bash
procler snippet list
procler snippet list --tag docker   # Filter by tag
procler snippet save --name rebuild --command 'docker compose build' --tags docker
procler snippet run rebuild
procler snippet remove rebuild
```

---

## Health Checks

Three probe types for monitoring process health:

```yaml
healthcheck:
  test: "curl -f http://localhost:8000/health"  # Command probe
  # OR
  http_get: "http://localhost:8000/health"      # HTTP GET probe (built-in)
  # OR
  tcp_socket: "localhost:5432"                  # TCP socket probe (built-in)
  interval: 10s
  timeout: 5s
  retries: 3
  start_period: 30s
```

---

## Export & Import

### Export to systemd
```bash
procler export systemd api          # Single process
procler export systemd --all        # All local processes
```

### Export to Docker Compose
```bash
procler export compose              # All processes as docker-compose.yml
```

### Import from Procfile
```bash
procler import procfile Procfile             # Import
procler import procfile Procfile --dry-run   # Preview only
procler import procfile Procfile --merge     # Merge into existing config
```

---

## Configuration

### Initialize
```bash
procler config init      # Creates .procler/ directory
procler config validate  # Validates config.yaml
procler config path      # Shows resolved paths
procler config explain   # Plain-language explanation
```

### Config Structure
```
.procler/
├── config.yaml    # Version-controllable definitions
├── changelog.log  # Audit trail of operations
└── state.db       # Runtime state (auto-gitignored)
```

### Full Config Example
```yaml
version: 1

vars:
  API_PORT: "8000"

processes:
  redis:
    command: redis-server
    context: local
    tags: [database, cache]

  api:
    command: uvicorn main:app --reload --port ${API_PORT}
    context: local
    cwd: /home/user/myapp
    tags: [backend]
    namespace: backend
    ready_log_line: "Uvicorn running on"
    max_memory: 512M
    healthcheck:
      http_get: "http://localhost:${API_PORT}/health"
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 30s
    depends_on:
      - redis

  worker:
    command: celery -A tasks worker
    context: docker
    container: myapp-worker
    replicas: 3
    depends_on:
      - name: api
        condition: healthy

  cleanup:
    command: python scripts/cleanup.py
    schedule: "0 */6 * * *"

groups:
  backend:
    description: "Full backend stack"
    processes: [redis, api, worker]

recipes:
  deploy:
    description: "Zero-downtime deployment"
    on_error: stop
    steps:
      - stop: worker
      - stop: api
      - exec: "alembic upgrade head"
      - start: api
      - start: worker

snippets:
  rebuild:
    command: docker compose build --no-cache
    description: "Rebuild all containers"
    tags: [docker, build]
```

---

## Web Server & API

```bash
procler serve                          # localhost:8000
procler serve --host 0.0.0.0 --port 8080
procler serve --reload                 # Development mode
```

### REST API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/processes | List all processes |
| GET | /api/processes/{name} | Get process details |
| POST | /api/processes | Create process |
| DELETE | /api/processes/{name} | Remove process |
| POST | /api/processes/{name}/start | Start process |
| POST | /api/processes/{name}/stop | Stop process |
| POST | /api/processes/{name}/restart | Restart process |
| GET | /api/logs/{name} | Get process logs |
| GET | /api/groups | List groups |
| POST | /api/groups/{name}/start | Start group |
| POST | /api/groups/{name}/stop | Stop group |
| GET | /api/groups/{name}/status | Group status |
| GET | /api/recipes | List recipes |
| POST | /api/recipes/{name}/run | Run recipe |
| GET | /api/snippets | List snippets |
| POST | /api/snippets | Create snippet |
| GET | /api/snippets/{name} | Get snippet |
| DELETE | /api/snippets/{name} | Remove snippet |
| POST | /api/snippets/{name}/run | Run snippet |
| GET | /api/config | Config status |
| POST | /api/config/reload | Reload config |
| GET | /api/config/export/{format} | Export (systemd, compose) |
| GET | /api/health | Health check |

### WebSocket
Connect to `ws://localhost:8000/api/ws` for real-time updates:
```json
{"action": "subscribe_logs", "process_id": 1}
{"action": "subscribe_status", "process_id": 1}
{"action": "subscribe_status"}
```

---

## Common Workflows

### Start Development Environment
```bash
procler group start backend
procler status
```

### Debug Failing Process
```bash
procler status api           # Check status and Linux state
procler logs api --tail 100  # View recent logs
procler restart api --clear-logs
```

### Graceful Deployment
```bash
procler recipe run deploy --dry-run   # Preview
procler recipe run deploy             # Execute
```

### Quick Command Execution
```bash
procler exec "npm run build" --cwd /app
procler exec "python manage.py migrate" --context docker --container myapp
```

### Migrate from Foreman/Overmind
```bash
procler import procfile Procfile --dry-run  # Preview
procler import procfile Procfile            # Import
```

### Export for Production
```bash
procler export systemd --all    # Generate systemd units
procler export compose          # Generate docker-compose.yml
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PROCLER_LOG_LEVEL` | `INFO` | DEBUG, INFO, WARNING, ERROR |
| `PROCLER_LOG_FILE` | - | Log file path (auto-rotates) |
| `PROCLER_LOG_ROTATION_INTERVAL` | `3600` | Seconds between log rotation |
| `PROCLER_MAX_LOGS_PER_PROCESS` | `10000` | Max log entries per process |
| `PROCLER_CONFIG_DIR` | `.procler/` | Config directory path |
| `PROCLER_DB_PATH` | `.procler/state.db` | Database path |
| `PROCLER_CORS_ORIGINS` | localhost | Allowed CORS origins |
| `PROCLER_DEBUG` | - | Enable detailed error messages |

---

## Error Codes

| Code | Description | Recovery |
|------|-------------|----------|
| `process_not_found` | Process doesn't exist | Run `procler list` |
| `process_exists` | Process name already taken | Choose different name or remove first |
| `process_running` | Operation invalid while running | Stop first |
| `process_stopped` | Operation invalid while stopped | Start first |
| `missing_container` | Docker context requires container | Add `--container` |
| `config_not_found` | No config.yaml | Run `procler config init` |
| `config_exists` | Config already exists | Use `--force` |
| `validation_failed` | Invalid config | Check error details |
| `group_not_found` | Group not in config | Check config.yaml |
| `recipe_not_found` | Recipe not in config | Check config.yaml |

---

## Docker Deployment

```bash
# Using Docker Compose
docker compose up -d

# Manual
docker build -t procler .
docker run -d -p 8000:8000 -v procler-data:/home/procler/.procler procler
```

### Production Features
- **Process Recovery**: Detects orphaned processes on startup
- **Graceful Shutdown**: SIGTERM/SIGINT triggers orderly process shutdown
- **Log Rotation**: Background task rotates logs hourly
- **Health Check**: `/api/health` endpoint for container health

---

## Tips for Agents

1. **Always parse JSON output** - Never assume command success from exit code alone
2. **Use `capabilities` for discovery** - Dynamically learn available commands
3. **Check `suggestion` on errors** - Contains actionable recovery steps
4. **Leverage idempotency** - Safe to retry start/stop operations
5. **Use `--dry-run` for recipes** - Preview destructive operations
6. **Monitor Linux state** - D and Z states require special handling
7. **Use groups for complex startups** - Dependencies are resolved automatically
8. **Clear logs on restart** - Use `--clear-logs` when debugging fresh starts
9. **Use namespaces** - Filter processes with `--namespace` for large setups
10. **Export for production** - Use `export` commands to generate deployment configs
