"""Configuration schema for procler using Pydantic."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ContextType(str, Enum):
    """Execution context type."""
    LOCAL = "local"
    DOCKER = "docker"


class OnErrorAction(str, Enum):
    """What to do when a recipe step fails."""
    STOP = "stop"
    CONTINUE = "continue"


class ProcessDef(BaseModel):
    """Process definition from config file."""
    command: str
    context: ContextType = ContextType.LOCAL
    container: str | None = None
    cwd: str | None = None
    tags: list[str] = Field(default_factory=list)
    description: str | None = None

    @field_validator("container")
    @classmethod
    def docker_requires_container(cls, v, info):
        """Validate that docker context has container name."""
        # Note: This runs per-field, full validation in model_validator
        return v


class GroupDef(BaseModel):
    """Process group definition."""
    processes: list[str]
    description: str | None = None
    stop_order: list[str] | None = None  # If None, reverse of processes

    def get_stop_order(self) -> list[str]:
        """Get the stop order (explicit or reversed start order)."""
        if self.stop_order:
            return self.stop_order
        return list(reversed(self.processes))


class RecipeStepStart(BaseModel):
    """Start a process."""
    start: str


class RecipeStepStop(BaseModel):
    """Stop a process."""
    stop: str
    ignore_error: bool = False


class RecipeStepRestart(BaseModel):
    """Restart a process."""
    restart: str


class RecipeStepGroupStart(BaseModel):
    """Start a process group."""
    group_start: str


class RecipeStepGroupStop(BaseModel):
    """Stop a process group."""
    group_stop: str


class RecipeStepWait(BaseModel):
    """Wait for a duration."""
    wait: str  # e.g., "2s", "500ms", "1m"

    def get_seconds(self) -> float:
        """Parse duration string to seconds."""
        duration = self.wait.strip().lower()
        if duration.endswith("ms"):
            return float(duration[:-2]) / 1000
        elif duration.endswith("s"):
            return float(duration[:-1])
        elif duration.endswith("m"):
            return float(duration[:-1]) * 60
        else:
            # Assume seconds if no unit
            return float(duration)


class RecipeStepExec(BaseModel):
    """Execute an arbitrary command."""
    exec: str
    context: ContextType = ContextType.LOCAL
    container: str | None = None
    cwd: str | None = None
    timeout: str = "60s"  # Default 60 second timeout
    ignore_error: bool = False

    def get_timeout_seconds(self) -> float:
        """Parse timeout string to seconds."""
        timeout = self.timeout.strip().lower()
        if timeout.endswith("ms"):
            return float(timeout[:-2]) / 1000
        elif timeout.endswith("s"):
            return float(timeout[:-1])
        elif timeout.endswith("m"):
            return float(timeout[:-1]) * 60
        else:
            return float(timeout)


# Union type for all recipe steps
RecipeStep = (
    RecipeStepStart
    | RecipeStepStop
    | RecipeStepRestart
    | RecipeStepGroupStart
    | RecipeStepGroupStop
    | RecipeStepWait
    | RecipeStepExec
)


def parse_recipe_step(step_data: dict) -> RecipeStep:
    """Parse a recipe step from dict to the appropriate type."""
    if "start" in step_data:
        return RecipeStepStart(**step_data)
    elif "stop" in step_data:
        return RecipeStepStop(**step_data)
    elif "restart" in step_data:
        return RecipeStepRestart(**step_data)
    elif "group_start" in step_data:
        return RecipeStepGroupStart(**step_data)
    elif "group_stop" in step_data:
        return RecipeStepGroupStop(**step_data)
    elif "wait" in step_data:
        return RecipeStepWait(**step_data)
    elif "exec" in step_data:
        return RecipeStepExec(**step_data)
    else:
        raise ValueError(f"Unknown recipe step type: {step_data}")


class RecipeDef(BaseModel):
    """Recipe definition - multi-step operation."""
    description: str | None = None
    steps: list[dict]  # Raw dicts, parsed lazily
    on_error: OnErrorAction = OnErrorAction.STOP

    def get_steps(self) -> list[RecipeStep]:
        """Parse and return typed steps."""
        return [parse_recipe_step(s) for s in self.steps]


class SnippetDef(BaseModel):
    """Snippet definition - simple reusable command."""
    command: str
    description: str | None = None
    context: ContextType = ContextType.LOCAL
    container: str | None = None
    tags: list[str] = Field(default_factory=list)


class ProclerConfig(BaseModel):
    """Root configuration object."""
    version: int = 1
    processes: dict[str, ProcessDef] = Field(default_factory=dict)
    groups: dict[str, GroupDef] = Field(default_factory=dict)
    recipes: dict[str, RecipeDef] = Field(default_factory=dict)
    snippets: dict[str, SnippetDef] = Field(default_factory=dict)

    def validate_references(self) -> list[str]:
        """Validate that all references exist. Returns list of errors."""
        errors = []

        # Check group process references
        for group_name, group in self.groups.items():
            for proc in group.processes:
                if proc not in self.processes:
                    errors.append(
                        f"Group '{group_name}' references unknown process '{proc}'"
                    )
            if group.stop_order:
                for proc in group.stop_order:
                    if proc not in self.processes:
                        errors.append(
                            f"Group '{group_name}' stop_order references unknown process '{proc}'"
                        )

        # Check recipe references
        for recipe_name, recipe in self.recipes.items():
            for i, step_data in enumerate(recipe.steps):
                if "start" in step_data and step_data["start"] not in self.processes:
                    errors.append(
                        f"Recipe '{recipe_name}' step {i+1} references unknown process '{step_data['start']}'"
                    )
                if "stop" in step_data and step_data["stop"] not in self.processes:
                    errors.append(
                        f"Recipe '{recipe_name}' step {i+1} references unknown process '{step_data['stop']}'"
                    )
                if "restart" in step_data and step_data["restart"] not in self.processes:
                    errors.append(
                        f"Recipe '{recipe_name}' step {i+1} references unknown process '{step_data['restart']}'"
                    )
                if "group_start" in step_data and step_data["group_start"] not in self.groups:
                    errors.append(
                        f"Recipe '{recipe_name}' step {i+1} references unknown group '{step_data['group_start']}'"
                    )
                if "group_stop" in step_data and step_data["group_stop"] not in self.groups:
                    errors.append(
                        f"Recipe '{recipe_name}' step {i+1} references unknown group '{step_data['group_stop']}'"
                    )

        # Check docker contexts have containers
        for name, proc in self.processes.items():
            if proc.context == ContextType.DOCKER and not proc.container:
                errors.append(
                    f"Process '{name}' has docker context but no container specified"
                )

        for name, snippet in self.snippets.items():
            if snippet.context == ContextType.DOCKER and not snippet.container:
                errors.append(
                    f"Snippet '{name}' has docker context but no container specified"
                )

        return errors
