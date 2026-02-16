"""Snippet management API routes."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ...core import SnippetManager
from ..deps import get_snippets

router = APIRouter()


class SnippetCreateRequest(BaseModel):
    """Request body for creating a snippet."""

    name: str
    command: str
    description: str | None = None
    context_type: str = "local"
    container_name: str | None = None
    tags: list[str] | None = None


class SnippetResponse(BaseModel):
    """Standard response wrapper for snippets."""

    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None
    error_code: str | None = None
    suggestion: str | None = None


@router.get("")
async def list_snippets(
    tag: str | None = Query(default=None, description="Filter by tag"),
    manager: SnippetManager = Depends(get_snippets),
) -> SnippetResponse:
    """List all snippets, optionally filtered by tag."""
    result = manager.list_snippets(tag=tag)
    return SnippetResponse(**result)


@router.post("")
async def create_snippet(
    request: SnippetCreateRequest,
    manager: SnippetManager = Depends(get_snippets),
) -> SnippetResponse:
    """Create a new snippet."""
    result = manager.save_snippet(
        name=request.name,
        command=request.command,
        description=request.description,
        context_type=request.context_type,
        container_name=request.container_name,
        tags=request.tags,
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result)

    return SnippetResponse(**result)


@router.get("/{name}")
async def get_snippet(
    name: str,
    manager: SnippetManager = Depends(get_snippets),
) -> SnippetResponse:
    """Get a specific snippet by name."""
    from sqler.query import SQLerField as F

    from ...db import init_database
    from ...models import Snippet

    init_database()

    results = Snippet.query().filter(F("name") == name).all()
    if not results:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "error": f"Snippet '{name}' not found",
                "error_code": "snippet_not_found",
            },
        )

    snippet = results[0]
    return SnippetResponse(
        success=True,
        data={
            "snippet": {
                "id": snippet._id,
                "name": snippet.name,
                "command": snippet.command,
                "description": snippet.description,
                "context_type": snippet.context_type,
                "container_name": snippet.container_name,
                "tags": snippet.tags or [],
                "created_at": snippet.created_at,
            }
        },
    )


@router.delete("/{name}")
async def delete_snippet(
    name: str,
    manager: SnippetManager = Depends(get_snippets),
) -> SnippetResponse:
    """Remove a snippet."""
    result = manager.remove_snippet(name)

    if not result["success"]:
        raise HTTPException(status_code=404, detail=result)

    return SnippetResponse(**result)


@router.post("/{name}/run")
async def run_snippet(
    name: str,
    manager: SnippetManager = Depends(get_snippets),
) -> SnippetResponse:
    """Run a snippet."""
    result = await manager.run_snippet(name)

    if not result["success"]:
        status_code = 404 if result.get("error_code") == "snippet_not_found" else 400
        raise HTTPException(status_code=status_code, detail=result)

    return SnippetResponse(**result)
