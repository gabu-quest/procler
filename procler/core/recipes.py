"""Recipe execution engine."""

from __future__ import annotations

import asyncio
import time
from typing import Any

from ..config import (
    ChangelogAction,
    OnErrorAction,
    RecipeDef,
    RecipeStepExec,
    RecipeStepGroupStart,
    RecipeStepGroupStop,
    RecipeStepRestart,
    RecipeStepStart,
    RecipeStepStop,
    RecipeStepWait,
    append_changelog,
    get_config,
)
from . import get_process_manager
from .events import EVENT_RECIPE_STEP, get_event_bus
from .groups import get_group_manager


class RecipeExecutor:
    """Executes multi-step recipes."""

    def __init__(self):
        self._process_manager = get_process_manager()
        self._group_manager = get_group_manager()

    def list_recipes(self) -> dict[str, Any]:
        """List all defined recipes."""
        config = get_config()

        recipes_data = []
        for name, recipe in config.recipes.items():
            recipes_data.append(
                {
                    "name": name,
                    "description": recipe.description,
                    "steps_count": len(recipe.steps),
                    "on_error": recipe.on_error.value,
                }
            )

        return {
            "success": True,
            "data": {
                "recipes": recipes_data,
                "count": len(recipes_data),
            },
        }

    def get_recipe(self, name: str) -> dict[str, Any]:
        """Get a specific recipe with full details."""
        config = get_config()

        if name not in config.recipes:
            return {
                "success": False,
                "error": f"Recipe '{name}' not found",
                "error_code": "recipe_not_found",
                "suggestion": "Run 'procler recipe list' to see available recipes",
            }

        recipe = config.recipes[name]
        return {
            "success": True,
            "data": {
                "recipe": {
                    "name": name,
                    "description": recipe.description,
                    "steps": recipe.steps,  # Raw steps for display
                    "on_error": recipe.on_error.value,
                }
            },
        }

    async def run_recipe(
        self,
        name: str,
        dry_run: bool = False,
        continue_on_error: bool | None = None,
    ) -> dict[str, Any]:
        """
        Execute a recipe.

        Args:
            name: Recipe name
            dry_run: If True, just show what would happen
            continue_on_error: Override recipe's on_error setting
        """
        config = get_config()

        if name not in config.recipes:
            return {
                "success": False,
                "error": f"Recipe '{name}' not found",
                "error_code": "recipe_not_found",
                "suggestion": "Run 'procler recipe list' to see available recipes",
            }

        recipe = config.recipes[name]
        steps = recipe.get_steps()

        # Determine error handling behavior
        if continue_on_error is not None:
            should_continue = continue_on_error
        else:
            should_continue = recipe.on_error == OnErrorAction.CONTINUE

        if dry_run:
            return self._dry_run(name, recipe, steps)

        # Execute for real
        start_time = time.time()
        results = []
        all_success = True
        stopped_at_step = None
        total_steps = len(steps)

        for i, step in enumerate(steps):
            step_num = i + 1
            action_desc = self._describe_step(step)

            # Emit "running" event before execution
            self._emit_step_event(name, step_num, total_steps, action_desc, "running")

            step_result = await self._execute_step(step, step_num)
            results.append(step_result)

            # Determine status for event
            if step_result["success"]:
                status = "success"
            elif step_result.get("ignore_error"):
                status = "warning"
            else:
                status = "error"

            # Emit completion event
            self._emit_step_event(name, step_num, total_steps, action_desc, status, error=step_result.get("error"))

            if not step_result["success"]:
                all_success = False
                if not should_continue and not step_result.get("ignore_error"):
                    stopped_at_step = step_num
                    # Emit skipped events for remaining steps
                    for j in range(i + 1, len(steps)):
                        skip_action = self._describe_step(steps[j])
                        self._emit_step_event(name, j + 1, total_steps, skip_action, "skipped")
                    break

        duration_ms = int((time.time() - start_time) * 1000)

        # Log execution to changelog
        append_changelog(
            action=ChangelogAction.EXECUTE,
            entity_type="recipe",
            entity_name=name,
            details={
                "duration_ms": duration_ms,
                "success": all_success,
                "steps_completed": len(results),
                "stopped_at": stopped_at_step,
            },
        )

        return {
            "success": all_success,
            "data": {
                "recipe": name,
                "duration_ms": duration_ms,
                "steps_total": len(steps),
                "steps_completed": len(results),
                "stopped_at_step": stopped_at_step,
                "results": results,
            },
        }

    def _dry_run(self, name: str, recipe: RecipeDef, steps: list) -> dict[str, Any]:
        """Show what a recipe would do without executing."""
        planned_steps = []

        for i, step in enumerate(steps):
            planned_steps.append(
                {
                    "step": i + 1,
                    "action": self._describe_step(step),
                }
            )

        return {
            "success": True,
            "data": {
                "recipe": name,
                "description": recipe.description,
                "dry_run": True,
                "planned_steps": planned_steps,
            },
        }

    def _emit_step_event(
        self,
        recipe: str,
        step: int,
        total: int,
        action: str,
        status: str,
        error: str | None = None,
    ) -> None:
        """Emit a recipe step event for real-time updates."""
        event_bus = get_event_bus()
        event_bus.emit_sync(
            EVENT_RECIPE_STEP,
            {
                "recipe": recipe,
                "step": step,
                "total": total,
                "action": action,
                "status": status,  # running, success, error, warning, skipped
                "error": error,
            },
        )

    def _describe_step(self, step) -> str:
        """Get a human-readable description of a step."""
        if isinstance(step, RecipeStepStart):
            return f"start process '{step.start}'"
        elif isinstance(step, RecipeStepStop):
            suffix = " (ignore_error)" if step.ignore_error else ""
            return f"stop process '{step.stop}'{suffix}"
        elif isinstance(step, RecipeStepRestart):
            return f"restart process '{step.restart}'"
        elif isinstance(step, RecipeStepGroupStart):
            return f"start group '{step.group_start}'"
        elif isinstance(step, RecipeStepGroupStop):
            return f"stop group '{step.group_stop}'"
        elif isinstance(step, RecipeStepWait):
            return f"wait {step.wait}"
        elif isinstance(step, RecipeStepExec):
            ctx = f" (docker:{step.container})" if step.container else ""
            suffix = " (ignore_error)" if step.ignore_error else ""
            return f"exec '{step.exec}'{ctx}{suffix}"
        else:
            return f"unknown step: {step}"

    async def _execute_step(self, step, step_num: int) -> dict[str, Any]:
        """Execute a single recipe step."""
        result = {
            "step": step_num,
            "action": self._describe_step(step),
            "success": True,
        }

        try:
            if isinstance(step, RecipeStepStart):
                res = await self._process_manager.start(step.start)
                result["success"] = res["success"]
                result["details"] = res.get("data") or {"error": res.get("error")}

            elif isinstance(step, RecipeStepStop):
                res = await self._process_manager.stop(step.stop)
                result["success"] = res["success"]
                result["details"] = res.get("data") or {"error": res.get("error")}
                result["ignore_error"] = step.ignore_error

            elif isinstance(step, RecipeStepRestart):
                res = await self._process_manager.restart(step.restart)
                result["success"] = res["success"]
                result["details"] = res.get("data") or {"error": res.get("error")}

            elif isinstance(step, RecipeStepGroupStart):
                res = await self._group_manager.start_group(step.group_start)
                result["success"] = res["success"]
                result["details"] = res.get("data") or {"error": res.get("error")}

            elif isinstance(step, RecipeStepGroupStop):
                res = await self._group_manager.stop_group(step.group_stop)
                result["success"] = res["success"]
                result["details"] = res.get("data") or {"error": res.get("error")}

            elif isinstance(step, RecipeStepWait):
                seconds = step.get_seconds()
                await asyncio.sleep(seconds)
                result["details"] = {"waited_seconds": seconds}

            elif isinstance(step, RecipeStepExec):
                timeout = step.get_timeout_seconds()
                res = await self._process_manager.exec_command(
                    command=step.exec,
                    context_type=step.context.value,
                    container_name=step.container,
                    cwd=step.cwd,
                    timeout=timeout,
                )
                result["success"] = res["success"]
                result["details"] = res.get("data") or {"error": res.get("error")}
                result["ignore_error"] = step.ignore_error

            else:
                result["success"] = False
                result["error"] = f"Unknown step type: {type(step)}"

        except Exception as e:
            result["success"] = False
            result["error"] = str(e)

        return result


# Singleton
_recipe_executor: RecipeExecutor | None = None


def get_recipe_executor() -> RecipeExecutor:
    """Get the singleton RecipeExecutor instance."""
    global _recipe_executor
    if _recipe_executor is None:
        _recipe_executor = RecipeExecutor()
    return _recipe_executor


def reset_recipe_executor() -> None:
    """Reset the singleton (for testing)."""
    global _recipe_executor
    _recipe_executor = None
