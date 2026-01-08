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
    read_changelog,
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
async def get_changelog(tail: int = 50, format: str = "parsed") -> ConfigResponse:
    """
    Get recent changelog entries.

    Args:
        tail: Number of entries to return (default 50)
        format: "parsed" for structured JSON entries, "raw" for text lines
    """
    changelog_path = get_changelog_path()

    if not changelog_path.exists():
        return ConfigResponse(
            success=True,
            data={
                "entries": [],
                "count": 0,
                "format": format,
            },
        )

    try:
        if format == "parsed":
            # Return structured JSON entries - LLM-friendly
            all_entries = read_changelog()
            entries = all_entries[-tail:] if len(all_entries) > tail else all_entries
            return ConfigResponse(
                success=True,
                data={
                    "entries": entries,
                    "count": len(entries),
                    "total": len(all_entries),
                    "format": "parsed",
                },
            )
        else:
            # Return raw lines
            lines = changelog_path.read_text().strip().splitlines()
            recent_lines = lines[-tail:] if len(lines) > tail else lines
            entries = [line for line in recent_lines if line.strip()]
            return ConfigResponse(
                success=True,
                data={
                    "entries": entries,
                    "count": len(entries),
                    "total": len(lines),
                    "format": "raw",
                },
            )
    except Exception as e:
        return ConfigResponse(
            success=False,
            error=str(e),
            error_code="changelog_error",
        )


@router.get("/explain")
async def explain_config() -> ConfigResponse:
    """
    Get a plain-language explanation of what the current config defines.

    This is designed for LLM consumption - it describes what the config
    will do in natural language.
    """
    config = get_config()
    config_path = get_config_file_path()

    if not config_path.exists():
        return ConfigResponse(
            success=True,
            data={
                "summary": "No config file found. Run 'procler config init' to create one.",
                "sections": [],
            },
        )

    sections = []

    # Explain processes
    if config.processes:
        proc_explanations = []
        for name, proc in config.processes.items():
            ctx = "locally" if proc.context.value == "local" else f"in Docker container '{proc.container}'"
            desc = f"'{name}': runs `{proc.command}` {ctx}"
            if proc.cwd:
                desc += f" (working dir: {proc.cwd})"
            if proc.description:
                desc += f" - {proc.description}"
            proc_explanations.append(desc)
        sections.append({
            "type": "processes",
            "title": f"{len(config.processes)} Process Definitions",
            "explanation": "These processes can be started, stopped, and monitored individually.",
            "items": proc_explanations,
        })

    # Explain groups
    if config.groups:
        group_explanations = []
        for name, group in config.groups.items():
            stop_order = group.get_stop_order()
            is_reversed = stop_order == list(reversed(group.processes))
            stop_desc = "reversed order" if is_reversed else f"custom order: {' → '.join(stop_order)}"
            desc = f"'{name}': starts [{' → '.join(group.processes)}], stops in {stop_desc}"
            if group.description:
                desc += f" - {group.description}"
            group_explanations.append(desc)
        sections.append({
            "type": "groups",
            "title": f"{len(config.groups)} Process Groups",
            "explanation": "Groups start processes in order and stop them in reverse (or custom) order.",
            "items": group_explanations,
        })

    # Explain recipes
    if config.recipes:
        recipe_explanations = []
        for name, recipe in config.recipes.items():
            steps = recipe.get_steps()
            step_summary = f"{len(steps)} steps"
            error_handling = "stops on error" if recipe.on_error.value == "stop" else "continues on error"
            desc = f"'{name}': {step_summary}, {error_handling}"
            if recipe.description:
                desc += f" - {recipe.description}"
            recipe_explanations.append(desc)
        sections.append({
            "type": "recipes",
            "title": f"{len(config.recipes)} Recipes",
            "explanation": "Recipes are multi-step operations that automate common workflows.",
            "items": recipe_explanations,
        })

    # Explain snippets
    if config.snippets:
        snippet_explanations = []
        for name, snippet in config.snippets.items():
            ctx = "locally" if snippet.context.value == "local" else f"in Docker '{snippet.container}'"
            desc = f"'{name}': `{snippet.command}` ({ctx})"
            if snippet.description:
                desc += f" - {snippet.description}"
            snippet_explanations.append(desc)
        sections.append({
            "type": "snippets",
            "title": f"{len(config.snippets)} Snippets",
            "explanation": "Snippets are reusable commands you can run quickly.",
            "items": snippet_explanations,
        })

    # Build summary
    total = len(config.processes) + len(config.groups) + len(config.recipes) + len(config.snippets)
    summary = f"Config defines {total} items: {len(config.processes)} processes, {len(config.groups)} groups, {len(config.recipes)} recipes, {len(config.snippets)} snippets."

    return ConfigResponse(
        success=True,
        data={
            "summary": summary,
            "sections": sections,
            "config_file": str(config_path),
        },
    )
