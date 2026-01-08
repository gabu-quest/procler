"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .. import __version__


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

    # Configure CORS for development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    from .routes import logs, processes, snippets, ws

    app.include_router(processes.router, prefix="/api/processes", tags=["processes"])
    app.include_router(logs.router, prefix="/api/logs", tags=["logs"])
    app.include_router(snippets.router, prefix="/api/snippets", tags=["snippets"])
    app.include_router(ws.router, prefix="/api", tags=["websocket"])

    @app.get("/api/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "version": __version__}

    return app


# Create default app instance
app = create_app()
