"""Process management API routes."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ...core import ProcessManager
from ..deps import get_manager

router = APIRouter()


class ProcessDefineRequest(BaseModel):
    """Request body for defining a process."""

    name: str
    command: str
    context_type: str = "local"
    container_name: str | None = None
    cwd: str | None = None
    display_name: str | None = None
    tags: list[str] | None = None


class ProcessResponse(BaseModel):
    """Standard response wrapper."""

    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None
    error_code: str | None = None
    suggestion: str | None = None


@router.get("")
async def list_processes(manager: ProcessManager = Depends(get_manager)) -> ProcessResponse:
    """List all process definitions."""
    result = await manager.status()
    return ProcessResponse(**result)


@router.get("/{name}")
async def get_process(
    name: str,
    manager: ProcessManager = Depends(get_manager),
) -> ProcessResponse:
    """Get a specific process by name."""
    result = await manager.status(name)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result)
    return ProcessResponse(**result)


@router.post("")
async def create_process(
    request: ProcessDefineRequest,
    manager: ProcessManager = Depends(get_manager),
) -> ProcessResponse:
    """Create or update a process definition."""
    from datetime import datetime

    from sqler.query import SQLerField as F

    from ...db import init_database
    from ...models import Process

    init_database()

    # Check if context is docker and container is missing
    if request.context_type == "docker" and not request.container_name:
        return ProcessResponse(
            success=False,
            error="Container name required for docker context",
            error_code="missing_container",
            suggestion="Provide container_name for docker context",
        )

    # Check if process already exists
    existing = Process.query().filter(F("name") == request.name).all()
    if existing:
        return ProcessResponse(
            success=False,
            error=f"Process '{request.name}' already exists",
            error_code="process_exists",
            suggestion=f"Use DELETE /api/processes/{request.name} first, or choose a different name",
        )

    process = Process(
        name=request.name,
        command=request.command,
        context_type=request.context_type,
        container_name=request.container_name,
        cwd=request.cwd,
        display_name=request.display_name,
        tags=request.tags,
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
    )
    process.save()

    return ProcessResponse(
        success=True,
        data={
            "action": "created",
            "process": {
                "id": process._id,
                "name": process.name,
                "command": process.command,
                "context_type": process.context_type,
            },
        },
    )


@router.delete("/{name}")
async def delete_process(
    name: str,
    manager: ProcessManager = Depends(get_manager),
) -> ProcessResponse:
    """Remove a process definition."""
    from sqler.query import SQLerField as F

    from ...db import init_database
    from ...models import Process

    init_database()

    results = Process.query().filter(F("name") == name).all()
    if not results:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "error": f"Process '{name}' not found",
                "error_code": "process_not_found",
            },
        )

    results[0].delete()
    return ProcessResponse(
        success=True,
        data={"action": "removed", "name": name},
    )


@router.post("/{name}/start")
async def start_process(
    name: str,
    manager: ProcessManager = Depends(get_manager),
) -> ProcessResponse:
    """Start a process."""
    result = await manager.start(name)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result)
    return ProcessResponse(**result)


@router.post("/{name}/stop")
async def stop_process(
    name: str,
    manager: ProcessManager = Depends(get_manager),
) -> ProcessResponse:
    """Stop a process."""
    result = await manager.stop(name)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result)
    return ProcessResponse(**result)


@router.post("/{name}/restart")
async def restart_process(
    name: str,
    clear_logs: bool = False,
    manager: ProcessManager = Depends(get_manager),
) -> ProcessResponse:
    """Restart a process. Use ?clear_logs=true to delete old logs."""
    result = await manager.restart(name, clear_logs=clear_logs)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result)
    return ProcessResponse(**result)
