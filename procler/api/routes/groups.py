"""Group management API routes."""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from ...core.groups import get_group_manager

router = APIRouter()


class GroupResponse(BaseModel):
    """Standard response wrapper."""

    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None
    error_code: str | None = None
    suggestion: str | None = None


@router.get("")
async def list_groups() -> GroupResponse:
    """List all defined groups."""
    manager = get_group_manager()
    result = manager.list_groups()
    return GroupResponse(**result)


@router.get("/{name}")
async def get_group(name: str) -> GroupResponse:
    """Get a specific group by name."""
    manager = get_group_manager()
    result = manager.get_group(name)
    if not result["success"]:
        return GroupResponse(**result)
    return GroupResponse(**result)


@router.get("/{name}/status")
async def get_group_status(name: str) -> GroupResponse:
    """Get status of all processes in a group."""
    manager = get_group_manager()
    result = await manager.status_group(name)
    return GroupResponse(**result)


@router.post("/{name}/start")
async def start_group(name: str) -> GroupResponse:
    """Start all processes in a group in order."""
    manager = get_group_manager()
    result = await manager.start_group(name)
    return GroupResponse(**result)


@router.post("/{name}/stop")
async def stop_group(name: str) -> GroupResponse:
    """Stop all processes in a group in stop order."""
    manager = get_group_manager()
    result = await manager.stop_group(name)
    return GroupResponse(**result)
