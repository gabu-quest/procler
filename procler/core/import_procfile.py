"""Import Procfile format into Procler config."""

from __future__ import annotations

from pathlib import Path

import yaml

from ..config.schema import ProcessDef


def parse_procfile(content: str) -> dict[str, ProcessDef]:
    """Parse Procfile content into ProcessDef objects.

    Procfile format: each line is `name: command`
    Lines starting with # are comments.
    Blank lines are ignored.
    """
    processes: dict[str, ProcessDef] = {}

    for line_num, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()

        # Skip blank lines and comments
        if not stripped or stripped.startswith("#"):
            continue

        # Parse name: command
        if ":" not in stripped:
            raise ValueError(f"Line {line_num}: Invalid Procfile syntax (expected 'name: command'): {stripped}")

        name, _, command = stripped.partition(":")
        name = name.strip()
        command = command.strip()

        if not name:
            raise ValueError(f"Line {line_num}: Empty process name")
        if not command:
            raise ValueError(f"Line {line_num}: Empty command for process '{name}'")

        # Validate name (alphanumeric, hyphens, underscores)
        if not all(c.isalnum() or c in "-_" for c in name):
            raise ValueError(
                f"Line {line_num}: Invalid process name '{name}' " "(only alphanumeric, hyphens, underscores allowed)"
            )

        if name in processes:
            raise ValueError(f"Line {line_num}: Duplicate process name '{name}'")

        processes[name] = ProcessDef(command=command)

    return processes


def parse_procfile_from_path(path: Path) -> dict[str, ProcessDef]:
    """Parse a Procfile from a file path."""
    if not path.exists():
        raise FileNotFoundError(f"Procfile not found: {path}")

    content = path.read_text()
    return parse_procfile(content)


def generate_config_yaml(processes: dict[str, ProcessDef], existing_config: dict | None = None) -> str:
    """Generate YAML config string from parsed Procfile processes.

    If existing_config is provided, merges new processes into it.
    """
    if existing_config is None:
        config = {"version": 1, "processes": {}}
    else:
        config = dict(existing_config)
        if "processes" not in config:
            config["processes"] = {}

    for name, proc_def in processes.items():
        config["processes"][name] = {"command": proc_def.command}

    return yaml.dump(config, default_flow_style=False, sort_keys=False)
