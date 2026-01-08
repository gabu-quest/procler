# Procgler

**A process manager where Claude Code is a first-class citizen.**

Procgler gives developers (and their AI coding assistants) a single pane of glass for managing the chaos of modern development environments - where processes span local shells, Docker containers, and various execution contexts.

## Features

- **Web Dashboard** - Visual monitoring, log viewing, one-click control
- **LLM-First CLI** - JSON-native commands designed for Claude Code integration
- **Dual Interface Parity** - CLI and Web UI share the same core logic
- **Context Abstraction** - Manage local processes and Docker containers uniformly

## Installation

```bash
pip install procgler
```

Or install from source:

```bash
git clone https://github.com/yourusername/procgler.git
cd procgler
uv sync
```

## Quick Start

```bash
# Define a process
procgler define --name my-api --command "uvicorn main:app --port 8000"

# Start it
procgler start my-api

# Check status (JSON output)
procgler status my-api

# View logs
procgler logs my-api --tail 50

# Stop it
procgler stop my-api
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

## Web Dashboard

```bash
procgler serve
# Open http://localhost:8000
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11+, FastAPI |
| Database | SQLite via sqler |
| Frontend | Vue 3, Vite, Pinia |
| CLI | Click |
| Docker | docker-py SDK |
| Real-time | WebSockets |

## Development

```bash
# Install dev dependencies
uv sync

# Run tests
pytest

# Run CLI in development
python -m procgler --help

# Run dev server with hot reload
python -m procgler serve --reload
```

## License

MIT
