"""Config management API routes."""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from ...config import (
    get_config,
    reload_config,
    get_config_file_path,
    get_changelog_path,
    find_config_dir,
)

router = APIRouter()


class ConfigResponse(BaseModel):
    """Standard response wrapper."""

    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None
    error_code: str | None = None


@router.get("")
async def get_config_info() -> ConfigResponse:
    """Get current config status and overview."""
    try:
        config = get_config()
        config_path = get_config_file_path()
        changelog_path = get_changelog_path()
        config_dir = find_config_dir()

        return ConfigResponse(
            success=True,
            data={
                "config_dir": str(config_dir),
                "config_file": str(config_path),
                "config_exists": config_path.exists(),
                "changelog_file": str(changelog_path),
                "changelog_exists": changelog_path.exists(),
                "version": config.version,
                "stats": {
                    "processes": len(config.processes),
                    "groups": len(config.groups),
                    "recipes": len(config.recipes),
                    "snippets": len(config.snippets),
                },
            },
        )
    except Exception as e:
        return ConfigResponse(
            success=False,
            error=str(e),
            error_code="config_error",
        )


@router.get("/processes")
async def list_config_processes() -> ConfigResponse:
    """List all processes defined in config (not runtime DB)."""
    config = get_config()

    processes = []
    for name, proc in config.processes.items():
        processes.append({
            "name": name,
            "command": proc.command,
            "context": proc.context.value,
            "container": proc.container,
            "cwd": proc.cwd,
            "description": proc.description,
            "tags": proc.tags,
        })

    return ConfigResponse(
        success=True,
        data={
            "processes": processes,
            "count": len(processes),
        },
    )


@router.post("/reload")
async def reload_config_endpoint() -> ConfigResponse:
    """Reload config from disk."""
    try:
        config = reload_config()
        return ConfigResponse(
            success=True,
            data={
                "reloaded": True,
                "version": config.version,
                "stats": {
                    "processes": len(config.processes),
                    "groups": len(config.groups),
                    "recipes": len(config.recipes),
                    "snippets": len(config.snippets),
                },
            },
        )
    except Exception as e:
        return ConfigResponse(
            success=False,
            error=str(e),
            error_code="reload_error",
        )


@router.get("/changelog")
async def get_changelog(tail: int = 50) -> ConfigResponse:
    """Get recent changelog entries."""
    changelog_path = get_changelog_path()

    if not changelog_path.exists():
        return ConfigResponse(
            success=True,
            data={
                "entries": [],
                "count": 0,
            },
        )

    try:
        lines = changelog_path.read_text().strip().splitlines()
        # Get last N lines
        recent_lines = lines[-tail:] if len(lines) > tail else lines

        entries = []
        for line in recent_lines:
            if line.strip():
                entries.append(line)

        return ConfigResponse(
            success=True,
            data={
                "entries": entries,
                "count": len(entries),
                "total": len(lines),
            },
        )
    except Exception as e:
        return ConfigResponse(
            success=False,
            error=str(e),
            error_code="changelog_error",
        )
