"""Export process definitions to systemd units and Docker Compose files."""

from __future__ import annotations

from ..config.schema import ProcessDef


def export_systemd_unit(
    name: str,
    proc_def: ProcessDef,
    description: str | None = None,
) -> str:
    """Generate a systemd .service unit file for a process definition.

    Args:
        name: Process name (used for the service name)
        proc_def: Process definition from config
        description: Optional override for the Description field

    Returns:
        String content of the .service unit file
    """
    desc = description or proc_def.description or f"Procler: {name}"
    working_dir = proc_def.cwd or ""

    lines = [
        "[Unit]",
        f"Description={desc}",
        "After=network-online.target",
        "Wants=network-online.target",
        "",
        "[Service]",
        "Type=simple",
        f"ExecStart={proc_def.command}",
    ]

    if working_dir:
        lines.append(f"WorkingDirectory={working_dir}")

    lines.extend(
        [
            "Restart=on-failure",
            "RestartSec=5",
            "StandardOutput=journal",
            "StandardError=journal",
        ]
    )

    if proc_def.max_memory:
        lines.append(f"MemoryMax={proc_def.max_memory}")

    lines.extend(
        [
            "",
            "[Install]",
            "WantedBy=multi-user.target",
            "",
        ]
    )

    return "\n".join(lines)


def export_compose(
    processes: dict[str, ProcessDef],
    project_name: str | None = None,
) -> str:
    """Generate a docker-compose.yml from process definitions.

    Args:
        processes: Dict of process name -> ProcessDef
        project_name: Optional project name for the compose file

    Returns:
        String content of the docker-compose.yml
    """
    lines = []

    if project_name:
        lines.append(f"name: {project_name}")
        lines.append("")

    lines.append("services:")

    for name, proc_def in processes.items():
        lines.append(f"  {name}:")

        if proc_def.context.value == "docker" and proc_def.container:
            lines.append(f"    container_name: {proc_def.container}")

        lines.append(f"    command: {proc_def.command}")

        if proc_def.cwd:
            lines.append(f"    working_dir: {proc_def.cwd}")

        if proc_def.description:
            lines.append(f"    # {proc_def.description}")

        # Map depends_on
        deps = proc_def.get_dependencies()
        if deps:
            lines.append("    depends_on:")
            for dep in deps:
                if dep.condition.value == "healthy":
                    lines.append(f"      {dep.name}:")
                    lines.append("        condition: service_healthy")
                elif dep.condition.value == "log_ready":
                    lines.append(f"      {dep.name}:")
                    lines.append("        condition: service_started")
                    lines.append("        # NOTE: log_ready condition not natively supported in Compose")
                else:
                    lines.append(f"      {dep.name}:")
                    lines.append("        condition: service_started")

        # Map healthcheck
        if proc_def.healthcheck:
            hc = proc_def.healthcheck
            lines.append("    healthcheck:")
            if hc.test:
                lines.append(f'      test: ["CMD-SHELL", "{hc.test}"]')
            elif hc.http_get:
                lines.append(f'      test: ["CMD-SHELL", "curl -f {hc.http_get} || exit 1"]')
            elif hc.tcp_socket:
                host_port = hc.tcp_socket
                if ":" in host_port:
                    host, port = host_port.rsplit(":", 1)
                    lines.append(f'      test: ["CMD-SHELL", "nc -z {host} {port} || exit 1"]')
            lines.append(f"      interval: {hc.interval}")
            lines.append(f"      timeout: {hc.timeout}")
            lines.append(f"      retries: {hc.retries}")
            if hc.start_period != "0s":
                lines.append(f"      start_period: {hc.start_period}")

        # Memory limit
        if proc_def.max_memory:
            lines.append("    deploy:")
            lines.append("      resources:")
            lines.append("        limits:")
            lines.append(f"          memory: {proc_def.max_memory}")

        # Tags as labels
        if proc_def.tags:
            lines.append("    labels:")
            for tag in proc_def.tags:
                lines.append(f"      procler.tag.{tag}: 'true'")

        lines.append("")

    return "\n".join(lines)
