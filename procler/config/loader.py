"""Config file discovery and loading."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

import yaml

from .schema import ProclerConfig

# Singleton config cache
_config_cache: ProclerConfig | None = None
_config_dir_cache: Path | None = None


def find_git_root() -> Path | None:
    """Find the root of the git repository, if any."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return Path(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def parse_env_file(path: Path) -> dict[str, str]:
    """Parse a simple .env file (KEY=value format)."""
    env = {}
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                # Strip quotes if present
                value = value.strip().strip('"').strip("'")
                env[key.strip()] = value
    return env


def find_config_dir(start_dir: Path | None = None) -> Path:
    """
    Find the procler config directory using this discovery chain:

    1. PROCLER_CONFIG_DIR environment variable
    2. .procler.env file in current dir or parents (sets PROCLER_CONFIG_DIR)
    3. .procler/ directory in current dir
    4. .procler/ directory in git root
    5. ~/.procler/ (global fallback)
    """
    global _config_dir_cache
    if _config_dir_cache is not None:
        return _config_dir_cache

    start = start_dir or Path.cwd()

    # 1. Explicit environment variable
    if env_dir := os.environ.get("PROCLER_CONFIG_DIR"):
        _config_dir_cache = Path(env_dir).expanduser().resolve()
        return _config_dir_cache

    # 2. Search for .procler.env in current dir and parents
    for parent in [start] + list(start.parents):
        env_file = parent / ".procler.env"
        if env_file.exists():
            env = parse_env_file(env_file)
            if config_dir := env.get("PROCLER_CONFIG_DIR"):
                # Resolve relative to the .procler.env location
                resolved = (parent / config_dir).resolve()
                _config_dir_cache = resolved
                return _config_dir_cache

    # 3. .procler/ in current directory
    local_config = start / ".procler"
    if local_config.exists() and local_config.is_dir():
        _config_dir_cache = local_config
        return _config_dir_cache

    # 4. .procler/ in git root
    git_root = find_git_root()
    if git_root:
        git_config = git_root / ".procler"
        if git_config.exists() and git_config.is_dir():
            _config_dir_cache = git_config
            return _config_dir_cache

    # 5. Global fallback
    _config_dir_cache = Path.home() / ".procler"
    return _config_dir_cache


def get_config_file_path() -> Path:
    """Get the path to the config.yaml file."""
    return find_config_dir() / "config.yaml"


def get_changelog_path() -> Path:
    """Get the path to the changelog.log file."""
    return find_config_dir() / "changelog.log"


def get_state_db_path() -> Path:
    """Get the path to the state.db file."""
    return find_config_dir() / "state.db"


def load_config(config_path: Path | None = None) -> ProclerConfig:
    """
    Load configuration from YAML file.

    Returns an empty config if no config file exists.
    """
    global _config_cache

    if config_path is None:
        config_path = get_config_file_path()

    if not config_path.exists():
        # Return empty config - processes/groups/recipes can be empty
        return ProclerConfig()

    with open(config_path) as f:
        data = yaml.safe_load(f) or {}

    config = ProclerConfig.model_validate(data)
    _config_cache = config
    return config


def get_config() -> ProclerConfig:
    """Get the cached config, loading if necessary."""
    global _config_cache
    if _config_cache is None:
        _config_cache = load_config()
    return _config_cache


def reload_config() -> ProclerConfig:
    """Force reload of config from disk."""
    global _config_cache
    _config_cache = None
    return load_config()


def save_config(config: ProclerConfig, config_path: Path | None = None) -> None:
    """Save configuration to YAML file."""
    if config_path is None:
        config_path = get_config_file_path()

    # Ensure directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert to dict, excluding defaults for cleaner output
    data = config.model_dump(exclude_defaults=True, exclude_none=True)

    # Always include version
    data["version"] = config.version

    with open(config_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def reset_config_cache() -> None:
    """Reset the config cache (useful for testing)."""
    global _config_cache, _config_dir_cache
    _config_cache = None
    _config_dir_cache = None


def generate_template_config() -> str:
    """Generate a template config.yaml with examples."""
    return '''\
# Procler Configuration - LLM-First Process Manager
# https://github.com/gabu-quest/procler
#
# This file is VERSION CONTROLLED - commit it to your repo!
# Each project can have its own .procler/ directory.
#
# Files in .procler/:
#   config.yaml   - This file (commit to git)
#   changelog.log - Audit trail of operations (commit to git)
#   state.db      - Runtime state (auto-gitignored)
#
# Discovery order: $PROCLER_CONFIG_DIR > .procler.env > .procler/ > git root > ~/.procler/
#
# CLI: `procler config explain` shows what this config does in plain language
# API: GET /api/config/explain returns the same as JSON
version: 1

# Process definitions - things that run continuously
processes:
  # Example local process
  # api:
  #   command: uvicorn main:app --reload
  #   context: local
  #   cwd: /path/to/project
  #   tags: [backend, api]
  #   description: "FastAPI development server"
  #
  # Example docker process
  # worker:
  #   command: celery -A app worker
  #   context: docker
  #   container: my-container
  #   description: "Background task worker"

# Process groups - ordered start/stop
# Use: `procler group start backend` / `procler group stop backend`
groups:
  # Example group
  # backend:
  #   description: "Full backend stack"
  #   processes: [redis, api, worker]  # Start in this order
  #   # stop_order defaults to reverse of processes
  #   # stop_order: [worker, api, redis]  # Custom stop order

# Recipes - multi-step operations (like makefiles for processes)
# Use: `procler recipe run deploy --dry-run` to preview
recipes:
  # Example recipe
  # deploy:
  #   description: "Graceful deployment with migration"
  #   on_error: stop  # or "continue"
  #   steps:
  #     - stop: worker
  #     - stop: api
  #     - wait: 2s
  #     - exec: "alembic upgrade head"
  #       context: docker
  #       container: my-container
  #     - start: api
  #     - start: worker

# Snippets - reusable one-off commands
# Use: `procler snippet run rebuild`
snippets:
  # Example snippet
  # rebuild:
  #   command: docker compose build
  #   description: "Rebuild all containers"
  #   tags: [docker, build]
'''
