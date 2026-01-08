"""FastAPI application factory."""

import os
import traceback
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .. import __version__

# Static files directory (where Vue build output goes)
STATIC_DIR = Path(__file__).parent.parent / "static"


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Procgler",
        description="LLM-first process manager for developers",
        version=__version__,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # Global exception handler for unexpected errors
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions with structured JSON response."""
        # Log the error for debugging
        error_trace = traceback.format_exc()
        print(f"Unexpected error: {exc}\n{error_trace}")

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Internal server error",
                "error_code": "internal_error",
                "detail": str(exc) if os.environ.get("PROCGLER_DEBUG") else None,
            },
        )

    # Configure CORS
    # In development, Vite runs on :5173 and proxies /api to backend
    # In production, everything is served from the same origin
    cors_origins = os.environ.get("PROCGLER_CORS_ORIGINS", "").split(",")
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
    from .routes import logs, processes, snippets, ws

    app.include_router(processes.router, prefix="/api/processes", tags=["processes"])
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
