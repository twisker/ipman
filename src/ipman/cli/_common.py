"""Shared CLI utilities."""

from __future__ import annotations

import click

from ipman.agents.base import AgentAdapter
from ipman.agents.registry import detect_agent, get_adapter


def resolve_agent(agent_name: str | None) -> AgentAdapter:
    """Resolve adapter from --agent flag or auto-detection."""
    if agent_name:
        return get_adapter(agent_name)
    detected = detect_agent()
    if detected is None:
        raise click.ClickException(
            "No agent detected. Use --agent to specify one "
            "(e.g. --agent claude-code)."
        )
    return detected
