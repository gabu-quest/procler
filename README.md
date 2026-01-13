# Procler

<img src="frontend/public/procler.png" alt="Procler logo" width="48" height="48" />

**A process manager where Claude Code is a first-class citizen.**

Procler gives developers (and their AI coding assistants) a single pane of glass for managing the chaos of modern development environments - where processes span local shells, Docker containers, and various execution contexts.

## Features

- **LLM-First CLI** - JSON-native commands designed for Claude Code integration
- **Web Dashboard** - Vue 3 dashboard with Cyberpunk design system, real-time updates
- **Dual Interface Parity** - CLI and Web UI share the same ProcessManager core
- **Context Abstraction** - Manage local processes and Docker containers uniformly
- **Snippets** - Save and reuse common commands with tagging
- **Real-time Updates** - WebSocket support for live status and log streaming
- **Config Variables** - Define `vars` in config.yaml and reference with `${VAR}`

## Installation

```bash
pip install procler
```

Or install from source:

```bash
git clone https://github.com/gabu-quest/procler.git
cd procler
uv pip install -e .[dev]
```

> **Note:** Frontend is pre-built and included. No separate build step needed!

## Quick Start

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

# Restart
procler restart my-api
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

## CLI Output

All CLI commands return structured JSON for easy parsing by scripts and LLMs:

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

Error responses include helpful context:

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
| `/api/snippets` | GET | List snippets (?tag=filter) |
| `/api/snippets` | POST | Create snippet |
| `/api/snippets/{name}` | GET | Get snippet |
| `/api/snippets/{name}` | DELETE | Remove snippet |
| `/api/snippets/{name}/run` | POST | Run snippet |
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

## Web Dashboard

The Vue 3 frontend provides a visual interface for managing processes and snippets:

- **Dashboard** - Overview of all processes with real-time status
- **Process List** - View all defined processes with start/stop/restart controls
- **Process Detail** - Live log streaming via WebSocket, process info
- **Snippets** - Save, manage, and run reusable commands
- **Groups & Recipes** - Manage process groups and multi-step operations

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

## License

MIT
