"""Recipe management API routes."""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from ...core.recipes import get_recipe_executor

router = APIRouter()


class RecipeResponse(BaseModel):
    """Standard response wrapper."""

    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None
    error_code: str | None = None
    suggestion: str | None = None


class RunRecipeRequest(BaseModel):
    """Request body for running a recipe."""

    dry_run: bool = False
    continue_on_error: bool | None = None


@router.get("")
async def list_recipes() -> RecipeResponse:
    """List all defined recipes."""
    executor = get_recipe_executor()
    result = executor.list_recipes()
    return RecipeResponse(**result)


@router.get("/{name}")
async def get_recipe(name: str) -> RecipeResponse:
    """Get a specific recipe with full details."""
    executor = get_recipe_executor()
    result = executor.get_recipe(name)
    return RecipeResponse(**result)


@router.post("/{name}/run")
async def run_recipe(name: str, request: RunRecipeRequest | None = None) -> RecipeResponse:
    """
    Execute a recipe.

    Pass dry_run=true to preview what would happen without executing.
    Pass continue_on_error to override the recipe's default error handling.
    """
    executor = get_recipe_executor()
    req = request or RunRecipeRequest()
    result = await executor.run_recipe(
        name=name,
        dry_run=req.dry_run,
        continue_on_error=req.continue_on_error,
    )
    return RecipeResponse(**result)


@router.post("/{name}/dry-run")
async def dry_run_recipe(name: str) -> RecipeResponse:
    """Preview what a recipe would do without executing."""
    executor = get_recipe_executor()
    result = await executor.run_recipe(name=name, dry_run=True)
    return RecipeResponse(**result)
