"""FastAPI application factory."""

import asyncio
import os
import signal
import traceback
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .. import __version__
from ..logging import logger

# Static files directory (where Vue build output goes)
STATIC_DIR = Path(__file__).parent.parent / "static"

# Background task for log rotation
_log_rotation_task: asyncio.Task | None = None
_shutdown_event = asyncio.Event()


async def _log_rotation_loop():
    """Background task to rotate logs periodically."""
    from ..core import get_process_manager

    rotation_interval = int(os.environ.get("PROCLER_LOG_ROTATION_INTERVAL", 3600))  # 1 hour default
    max_logs = int(os.environ.get("PROCLER_MAX_LOGS_PER_PROCESS", 10000))

    logger.info(f"Log rotation started (interval={rotation_interval}s, max_logs={max_logs})")

    while not _shutdown_event.is_set():
        try:
            await asyncio.sleep(rotation_interval)
            if _shutdown_event.is_set():
                break

            manager = get_process_manager()
            rotated = await asyncio.to_thread(manager.cleanup_all_logs, max_logs)
            if rotated:
                logger.info(f"Rotated logs for {len(rotated)} processes")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Log rotation error: {e}")


async def _recover_processes():
    """Check for orphaned processes on startup and update their status."""
    from sqler.query import SQLerField as F

    from ..db import init_database
    from ..models import Process, ProcessStatus

    init_database()

    # Find processes marked as running
    all_procs = Process.query().all()
    running = [
        p for p in all_procs
        if p.status in [ProcessStatus.RUNNING.value, ProcessStatus.STARTING.value]
    ]

    if not running:
        return

    logger.info(f"Checking {len(running)} processes marked as running...")

    for proc in running:
        if proc.pid:
            # Check if PID is still running
            try:
                os.kill(proc.pid, 0)  # Signal 0 = check if process exists
                logger.debug(f"Process '{proc.name}' (PID {proc.pid}) is still running")
            except (OSError, ProcessLookupError):
                # Process is dead, update status
                logger.warning(f"Process '{proc.name}' (PID {proc.pid}) is dead, marking as stopped")
                proc.status = ProcessStatus.STOPPED.value
                proc.pid = None
                proc.save()
        else:
            # No PID but marked as running - mark as stopped
            logger.warning(f"Process '{proc.name}' has no PID but marked running, fixing")
            proc.status = ProcessStatus.STOPPED.value
            proc.save()


async def _graceful_shutdown():
    """Stop all running processes gracefully."""
    from ..core import get_process_manager

    # Check if already shutting down to prevent loops
    if _shutdown_event.is_set():
        return

    logger.info("Graceful shutdown initiated...")
    _shutdown_event.set()

    manager = get_process_manager()
    result = await manager.status()

    if result["success"]:
        running = [p for p in result["data"]["processes"] if p["status"] == "running"]
        if running:
            logger.info(f"Stopping {len(running)} running processes...")
            for proc in running:
                try:
                    await manager.stop(proc["name"], timeout=5.0)
                    logger.debug(f"Stopped '{proc['name']}'")
                except Exception as e:
                    logger.error(f"Failed to stop '{proc['name']}': {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown."""
    global _log_rotation_task

    # Startup
    logger.info(f"Procler v{__version__} starting...")

    # Recover orphaned processes
    await _recover_processes()

    # Start log rotation background task
    _log_rotation_task = asyncio.create_task(_log_rotation_loop())

    # Register signal handlers for graceful shutdown
    # Only trigger shutdown once even if signal received multiple times
    shutdown_triggered = False

    def handle_shutdown_signal():
        nonlocal shutdown_triggered
        if not shutdown_triggered:
            shutdown_triggered = True
            _shutdown_event.set()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, handle_shutdown_signal)
        except NotImplementedError:
            # Windows doesn't support add_signal_handler
            pass

    logger.info("Procler ready")

    yield

    # Shutdown
    logger.info("Procler shutting down...")

    # Cancel log rotation task
    if _log_rotation_task:
        _log_rotation_task.cancel()
        try:
            await _log_rotation_task
        except asyncio.CancelledError:
            pass

    # Graceful shutdown of processes
    await _graceful_shutdown()

    logger.info("Procler stopped")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Procler",
        description="LLM-first process manager for developers",
        version=__version__,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # Global exception handler for unexpected errors
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions with structured JSON response."""
        # Log the error for debugging
        logger.exception(f"Unexpected error handling {request.method} {request.url.path}")

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Internal server error",
                "error_code": "internal_error",
                "detail": str(exc) if os.environ.get("PROCLER_DEBUG") else None,
            },
        )

    # Configure CORS
    # In development, Vite runs on :5173 and proxies /api to backend
    # In production, everything is served from the same origin
    cors_origins = os.environ.get("PROCLER_CORS_ORIGINS", "").split(",")
    cors_origins = [o.strip() for o in cors_origins if o.strip()]

    # Default development origins
    if not cors_origins:
        cors_origins = [
            "http://localhost:5173",  # Vite dev server
            "http://127.0.0.1:5173",
            "http://localhost:8000",  # Same origin
            "http://127.0.0.1:8000",
        ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routers
    from .routes import config, groups, logs, processes, recipes, snippets, ws

    app.include_router(processes.router, prefix="/api/processes", tags=["processes"])
    app.include_router(groups.router, prefix="/api/groups", tags=["groups"])
    app.include_router(recipes.router, prefix="/api/recipes", tags=["recipes"])
    app.include_router(config.router, prefix="/api/config", tags=["config"])
    app.include_router(logs.router, prefix="/api/logs", tags=["logs"])
    app.include_router(snippets.router, prefix="/api/snippets", tags=["snippets"])
    app.include_router(ws.router, prefix="/api", tags=["websocket"])

    @app.get("/api/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "version": __version__}

    # Serve static files if they exist (production mode)
    if STATIC_DIR.exists() and (STATIC_DIR / "index.html").exists():
        # Mount static assets (js, css, etc.)
        app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

        # Serve index.html for SPA routing (catch-all for non-API routes)
        @app.get("/{full_path:path}")
        async def serve_spa(request: Request, full_path: str):
            """Serve the SPA for all non-API routes."""
            # Don't serve index.html for API routes
            if full_path.startswith("api/"):
                return JSONResponse(
                    {"success": False, "error": "Not found", "error_code": "not_found"},
                    status_code=404,
                )

            # Check if it's a static file request
            static_file = STATIC_DIR / full_path
            if static_file.exists() and static_file.is_file():
                return FileResponse(static_file)

            # Return index.html for SPA routing
            return FileResponse(STATIC_DIR / "index.html")

    return app


# Create default app instance
app = create_app()
