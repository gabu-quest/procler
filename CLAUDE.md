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
│   ├── models.py               # Dataclasses for type hints
│   ├── core/                   # Shared business logic
│   │   ├── process_manager.py  # Central coordinator
│   │   ├── context_base.py     # Abstract ExecutionContext
│   │   ├── context_local.py    # Subprocess implementation
│   │   ├── context_docker.py   # Docker SDK implementation
│   │   ├── log_collector.py    # Async log capture
│   │   └── snippets.py         # Snippet operations
│   └── api/                    # FastAPI application
│       ├── app.py              # App factory
│       ├── deps.py             # Dependency injection
│       └── routes/             # API endpoints
├── frontend/                   # Vue 3 dashboard (later phases)
└── tests/                      # pytest tests
```

---

## Tech Stack

- **Backend:** Python 3.12+, FastAPI, Click CLI
- **Database:** SQLite via [sqler](https://pypi.org/project/sqler/) (JSON-first micro-ORM)
- **Frontend:** Vue 3, Vite, Pinia (later phases)
- **Docker:** docker-py SDK for container operations
- **Real-time:** WebSockets (native FastAPI)

---

## Key Design Principles

1. **JSON-native CLI** - All commands return structured JSON, never human-formatted tables
2. **Idempotent operations** - Safe to retry; `start` on running process returns current state
3. **Dual interface parity** - CLI and Web UI share the same ProcessManager core
4. **Context abstraction** - Local and Docker execution are pluggable contexts

---

## Development

```bash
# Install dependencies
uv sync

# Run CLI
python -m procgler --help

# Run tests
pytest

# Run dev server (later phases)
python -m procgler serve --reload
```

---

## Roadmap Reference

See `procgler-roadmap.md` for the full implementation plan with phases and acceptance criteria.

---

## Working in This Repo

- All CLI output MUST be valid JSON
- Tests use pytest with pytest-asyncio
- Follow existing patterns in the codebase
- Keep the repo healthy - incremental commits, tests alongside changes
