# Procgler

**A process manager where Claude Code is a first-class citizen.**

Procgler gives developers (and their AI coding assistants) a single pane of glass for managing the chaos of modern development environments - where processes span local shells, Docker containers, and various execution contexts.

## Features

- **LLM-First CLI** - JSON-native commands designed for Claude Code integration
- **Web Dashboard** - REST API + WebSocket real-time updates (Vue frontend coming soon)
- **Dual Interface Parity** - CLI and Web UI share the same ProcessManager core
- **Context Abstraction** - Manage local processes and Docker containers uniformly
- **Snippets** - Save and reuse common commands with tagging
- **Real-time Updates** - WebSocket support for live status and log streaming

## Installation

```bash
pip install procgler
```

Or install from source:

```bash
git clone https://github.com/yourusername/procgler.git
cd procgler
uv sync --all-extras
```

## Quick Start

### Process Management

```bash
# Define a process
procgler define --name my-api --command "uvicorn main:app --port 8000"

# Start it
procgler start my-api

# Check status (JSON output)
procgler status my-api

# View logs
procgler logs my-api --tail 50 --since 5m

# Stop it
procgler stop my-api

# Restart
procgler restart my-api
```

### Docker Processes

```bash
# Define a process that runs in a Docker container
procgler define \
  --name db-migrate \
  --command "alembic upgrade head" \
  --context docker \
  --container api-container

# Execute arbitrary command in container
procgler exec "pip list" --context docker --container api-container
```

### Snippets (Reusable Commands)

```bash
# Save a snippet
procgler snippet save \
  --name rebuild-api \
  --command "docker compose build api" \
  --tags docker,build

# List snippets (with optional tag filter)
procgler snippet list --tag docker

# Run a snippet
procgler snippet run rebuild-api
```

### Web Server

```bash
# Start the API server
procgler serve --host 0.0.0.0 --port 8000

# With hot reload for development
procgler serve --reload
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
| Frontend | Vue 3, Vite, Pinia (coming soon) |
| CLI | Click |
| Docker | docker-py SDK |
| Real-time | WebSockets |

## Development

```bash
# Install dev dependencies
uv sync --all-extras

# Run tests (91 tests)
uv run pytest tests/ -v

# Run CLI in development
uv run python -m procgler --help

# Run dev server with hot reload
uv run python -m procgler serve --reload
```

## Claude Code Integration

Procgler is designed for seamless AI assistant integration:

```
Human: "My auth-api seems slow, check its recent logs and restart it if there are errors"

Claude Code:
1. procgler logs auth-api --tail 100
2. [Analyzes JSON log output]
3. procgler restart auth-api
4. procgler status auth-api
5. Reports back to human
```

## License

MIT
