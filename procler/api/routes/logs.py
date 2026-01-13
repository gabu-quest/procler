"""Log retrieval API routes."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ...core import ProcessManager
from ..deps import get_manager

router = APIRouter()


class LogsResponse(BaseModel):
    """Response for log queries."""

    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None
    error_code: str | None = None


@router.get("/{name}")
async def get_logs(
    name: str,
    tail: int = Query(default=100, ge=1, le=10000, description="Number of lines to return"),
    since: str | None = Query(default=None, description="Time filter (e.g., '5m', '1h', ISO timestamp)"),
    manager: ProcessManager = Depends(get_manager),
) -> LogsResponse:
    """
    Get logs for a process.

    Args:
        name: Process name
        tail: Number of lines to return (default: 100, max: 10000)
        since: Time filter (e.g., '5m', '1h', ISO timestamp)
    """
    result = await manager.logs(name, tail=tail, since=since)

    if not result["success"]:
        raise HTTPException(status_code=404, detail=result)

    return LogsResponse(**result)
