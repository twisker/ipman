"""Shared CLI utilities."""

from __future__ import annotations

from pathlib import Path

import click

from ipman.agents.base import AgentAdapter
from ipman.agents.registry import detect_agent, get_adapter


def _agent_from_active_env(project_path: Path | None = None) -> str | None:
    """Try to read the agent name from the currently active environment."""
    if project_path is None:
        project_path = Path.cwd()
    ipman_config = project_path / ".ipman" / "ipman.yaml"
    if not ipman_config.exists():
        return None
    try:
        import yaml
        config = yaml.safe_load(ipman_config.read_text(encoding="utf-8")) or {}
        agent_name = config.get("agent")
        if agent_name and agent_name != "auto":
            return str(agent_name)
    except Exception:
        pass
    return None


def resolve_agent(agent_name: str | None) -> AgentAdapter:
    """Resolve adapter from --agent flag, active env, or auto-detection."""
    if agent_name:
        return get_adapter(agent_name)

    # Try auto-detection from project config dir
    detected = detect_agent()
    if detected is not None:
        return detected

    # Try reading from active environment metadata
    active_agent = _agent_from_active_env()
    if active_agent:
        return get_adapter(active_agent)

    # Fallback: prefer first installed agent
    from ipman.agents.registry import detect_installed_agents
    installed = detect_installed_agents()
    if installed:
        return installed[0]

    raise click.ClickException(
        "No agent detected. Use --agent to specify one "
        "(e.g. --agent claude-code)."
    )
