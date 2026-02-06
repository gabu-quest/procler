"""Configuration schema for procler using Pydantic."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


def parse_memory_string(value: str) -> int:
    """Parse a memory string like '512M', '1G', '256K' to bytes.

    Supports: B, K/KB, M/MB, G/GB (case-insensitive).
    Returns bytes as an integer.
    """
    value = value.strip().upper()
    multipliers = {
        "B": 1,
        "K": 1024,
        "KB": 1024,
        "M": 1024 * 1024,
        "MB": 1024 * 1024,
        "G": 1024 * 1024 * 1024,
        "GB": 1024 * 1024 * 1024,
    }

    for suffix, multiplier in sorted(multipliers.items(), key=lambda x: -len(x[0])):
        if value.endswith(suffix):
            num_str = value[: -len(suffix)].strip()
            try:
                return int(float(num_str) * multiplier)
            except ValueError:
                raise ValueError(f"Invalid memory value: {value}")

    # Try as raw bytes
    try:
        return int(value)
    except ValueError:
        raise ValueError(f"Invalid memory format: {value}. Use format like '512M', '1G', '256K'")


class ContextType(str, Enum):
    """Execution context type."""

    LOCAL = "local"
    DOCKER = "docker"


class OnErrorAction(str, Enum):
    """What to do when a recipe step fails."""

    STOP = "stop"
    CONTINUE = "continue"


class HealthCheckDef(BaseModel):
    """Health check definition for a process.

    Exactly one of test, http_get, or tcp_socket must be specified.
    """

    test: str | None = None  # Command to run, e.g., "curl -f http://localhost:8000/health"
    http_get: str | None = None  # HTTP GET URL, e.g., "http://localhost:8000/health"
    tcp_socket: str | None = None  # TCP address, e.g., "localhost:5432"
    interval: str = "10s"  # Time between checks
    timeout: str = "5s"  # How long to wait for check to complete
    retries: int = 3  # Number of consecutive failures before unhealthy
    start_period: str = "0s"  # Grace period before checks start

    @model_validator(mode="after")
    def validate_probe_type(self):
        """Ensure exactly one probe type is specified."""
        probes = [self.test, self.http_get, self.tcp_socket]
        specified = sum(1 for p in probes if p is not None)
        if specified == 0:
            raise ValueError("Health check must specify one of: test, http_get, or tcp_socket")
        if specified > 1:
            raise ValueError("Health check must specify only one of: test, http_get, or tcp_socket")
        return self

    def get_interval_seconds(self) -> float:
        """Parse interval to seconds."""
        return self._parse_duration(self.interval)

    def get_timeout_seconds(self) -> float:
        """Parse timeout to seconds."""
        return self._parse_duration(self.timeout)

    def get_start_period_seconds(self) -> float:
        """Parse start_period to seconds."""
        return self._parse_duration(self.start_period)

    def _parse_duration(self, duration: str) -> float:
        """Parse duration string to seconds."""
        d = duration.strip().lower()
        if d.endswith("ms"):
            return float(d[:-2]) / 1000
        elif d.endswith("s"):
            return float(d[:-1])
        elif d.endswith("m"):
            return float(d[:-1]) * 60
        else:
            return float(d)


class DependencyCondition(str, Enum):
    """Conditions for process dependencies."""

    STARTED = "started"  # Just needs to be running
    HEALTHY = "healthy"  # Must pass health check
    LOG_READY = "log_ready"  # Must match ready_log_line regex in stdout


class DependencyDef(BaseModel):
    """Dependency definition for a process."""

    name: str  # Process name
    condition: DependencyCondition = DependencyCondition.STARTED


class ProcessDef(BaseModel):
    """Process definition from config file."""

    command: str
    context: ContextType = ContextType.LOCAL
    container: str | None = None
    cwd: str | None = None
    tags: list[str] = Field(default_factory=list)
    description: str | None = None
    healthcheck: HealthCheckDef | None = None
    depends_on: list[str | DependencyDef] = Field(default_factory=list)

    # Ready detection via log line (regex pattern matched against stdout/stderr)
    ready_log_line: str | None = None

    # Memory threshold for auto-restart (e.g., "512M", "1G", "256K")
    max_memory: str | None = None

    # Cron schedule (e.g., "0 */6 * * *" for every 6 hours)
    schedule: str | None = None

    # Daemon mode configuration
    daemon_mode: bool = False
    daemon_match_pattern: str | None = None
    daemon_pidfile: str | None = None
    daemon_container: str | None = None  # Container to detect daemon in (for docker exec commands)
    adopt_existing: bool = False

    def get_dependencies(self) -> list[DependencyDef]:
        """Get normalized dependency list."""
        deps = []
        for dep in self.depends_on:
            if isinstance(dep, str):
                deps.append(DependencyDef(name=dep))
            else:
                deps.append(dep)
        return deps

    @field_validator("container")
    @classmethod
    def docker_requires_container(cls, v, info):
        """Validate that docker context has container name."""
        # Note: This runs per-field, full validation in model_validator
        return v

    @model_validator(mode="after")
    def validate_daemon_mode(self):
        """Validate daemon mode configuration."""
        if self.daemon_mode:
            if not self.daemon_match_pattern and not self.daemon_pidfile:
                raise ValueError("daemon_mode requires either daemon_match_pattern or daemon_pidfile")
        if self.adopt_existing and not self.daemon_mode:
            raise ValueError("adopt_existing requires daemon_mode=true")
        return self


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
    vars: dict[str, str] = Field(default_factory=dict)  # Variable substitution
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
                    errors.append(f"Group '{group_name}' references unknown process '{proc}'")
            if group.stop_order:
                for proc in group.stop_order:
                    if proc not in self.processes:
                        errors.append(f"Group '{group_name}' stop_order references unknown process '{proc}'")

        # Check recipe references
        for recipe_name, recipe in self.recipes.items():
            for i, step_data in enumerate(recipe.steps):
                if "start" in step_data and step_data["start"] not in self.processes:
                    errors.append(
                        f"Recipe '{recipe_name}' step {i+1} references unknown process '{step_data['start']}'"
                    )
                if "stop" in step_data and step_data["stop"] not in self.processes:
                    errors.append(f"Recipe '{recipe_name}' step {i+1} references unknown process '{step_data['stop']}'")
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
                errors.append(f"Process '{name}' has docker context but no container specified")

        for name, snippet in self.snippets.items():
            if snippet.context == ContextType.DOCKER and not snippet.container:
                errors.append(f"Snippet '{name}' has docker context but no container specified")

        return errors
