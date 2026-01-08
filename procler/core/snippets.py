"""Snippet management for reusable commands."""

from datetime import datetime
from typing import Any

from sqler.query import SQLerField as F

from ..db import init_database
from ..models import Snippet
from .context_docker import is_docker_available
from .context_local import get_local_context


class SnippetManager:
    """Manager for command snippets."""

    def __init__(self):
        pass

    def _get_snippet_by_name(self, name: str) -> Snippet | None:
        """Get a snippet by name."""
        results = Snippet.query().filter(F("name") == name).all()
        return results[0] if results else None

    def _snippet_to_dict(self, snippet: Snippet) -> dict[str, Any]:
        """Convert a Snippet to a dict for JSON output."""
        return {
            "id": snippet._id,
            "name": snippet.name,
            "command": snippet.command,
            "description": snippet.description,
            "context_type": snippet.context_type,
            "container_name": snippet.container_name,
            "tags": snippet.tags or [],
            "created_at": snippet.created_at,
        }

    def list_snippets(self, tag: str | None = None) -> dict[str, Any]:
        """
        List all snippets, optionally filtered by tag.

        Args:
            tag: Optional tag to filter by

        Returns a dict with snippet list (for JSON output).
        """
        init_database()

        snippets = Snippet.query().all()

        if tag:
            # Filter by tag
            snippets = [s for s in snippets if s.tags and tag in s.tags]

        return {
            "success": True,
            "data": {
                "snippets": [self._snippet_to_dict(s) for s in snippets],
                "count": len(snippets),
            },
        }

    def save_snippet(
        self,
        name: str,
        command: str,
        description: str | None = None,
        context_type: str = "local",
        container_name: str | None = None,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Save a new snippet.

        Args:
            name: Unique snippet name
            command: Command to execute
            description: Optional description
            context_type: Execution context ('local' or 'docker')
            container_name: Docker container name (required if context=docker)
            tags: Optional list of tags

        Returns a dict with save result (for JSON output).
        """
        init_database()

        # Validate docker context
        if context_type == "docker" and not container_name:
            return {
                "success": False,
                "error": "Container name required for docker context",
                "error_code": "missing_container",
                "suggestion": "Use --container <name> to specify the Docker container",
            }

        # Check if snippet already exists
        existing = self._get_snippet_by_name(name)
        if existing:
            return {
                "success": False,
                "error": f"Snippet '{name}' already exists",
                "error_code": "snippet_exists",
                "suggestion": f"Use 'procler snippet remove {name}' first, or choose a different name",
            }

        snippet = Snippet(
            name=name,
            command=command,
            description=description,
            context_type=context_type,
            container_name=container_name,
            tags=tags,
            created_at=datetime.now().isoformat(),
        )
        snippet.save()

        return {
            "success": True,
            "data": {
                "action": "created",
                "snippet": self._snippet_to_dict(snippet),
            },
        }

    def remove_snippet(self, name: str) -> dict[str, Any]:
        """
        Remove a snippet by name.

        Returns a dict with removal result (for JSON output).
        """
        init_database()

        snippet = self._get_snippet_by_name(name)
        if not snippet:
            return {
                "success": False,
                "error": f"Snippet '{name}' not found",
                "error_code": "snippet_not_found",
                "suggestion": "Run 'procler snippet list' to see available snippets",
            }

        snippet.delete()

        return {
            "success": True,
            "data": {
                "action": "removed",
                "name": name,
            },
        }

    async def run_snippet(self, name: str) -> dict[str, Any]:
        """
        Run a snippet by name.

        Returns a dict with execution result (for JSON output).
        """
        init_database()

        snippet = self._get_snippet_by_name(name)
        if not snippet:
            return {
                "success": False,
                "error": f"Snippet '{name}' not found",
                "error_code": "snippet_not_found",
                "suggestion": "Run 'procler snippet list' to see available snippets",
            }

        # Validate docker context
        if snippet.context_type == "docker":
            if not snippet.container_name:
                return {
                    "success": False,
                    "error": "Snippet has docker context but no container name",
                    "error_code": "missing_container",
                }

            if not is_docker_available():
                return {
                    "success": False,
                    "error": "Docker is not available",
                    "error_code": "docker_unavailable",
                    "suggestion": "Ensure Docker is installed and running",
                }

            # Import here to avoid circular imports
            from .context_docker import get_docker_context

            context = get_docker_context()
            try:
                result = await context.exec_command(
                    command=snippet.command,
                    container_name=snippet.container_name,
                )
            except ValueError as e:
                return {
                    "success": False,
                    "error": str(e),
                    "error_code": "container_not_found",
                }
        else:
            # Local context
            context = get_local_context()
            result = await context.exec_command(command=snippet.command)

        return {
            "success": True,
            "data": {
                "snippet": name,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.exit_code,
            },
        }


# Global singleton
_snippet_manager: SnippetManager | None = None


def get_snippet_manager() -> SnippetManager:
    """Get the global SnippetManager instance."""
    global _snippet_manager
    if _snippet_manager is None:
        _snippet_manager = SnippetManager()
    return _snippet_manager
