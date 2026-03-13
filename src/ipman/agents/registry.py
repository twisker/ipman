"""Agent adapter registry."""

from __future__ import annotations

from pathlib import Path

from ipman.agents.base import AgentAdapter
from ipman.agents.claude_code import ClaudeCodeAdapter
from ipman.agents.openclaw import OpenClawAdapter

# All known adapters, in detection priority order
_ADAPTERS: list[AgentAdapter] = [
    ClaudeCodeAdapter(),
    OpenClawAdapter(),
]


def get_adapter(name: str) -> AgentAdapter:
    """Get an adapter by agent name."""
    for adapter in _ADAPTERS:
        if adapter.name == name:
            return adapter
    known = ", ".join(a.name for a in _ADAPTERS)
    msg = f"Unknown agent: '{name}'. Known agents: {known}"
    raise ValueError(msg)


def detect_agent(project_path: Path | None = None) -> AgentAdapter | None:
    """Auto-detect the agent used in a project directory."""
    if project_path is None:
        project_path = Path.cwd()
    for adapter in _ADAPTERS:
        if adapter.detect_in_project(project_path):
            return adapter
    return None


def detect_installed_agents() -> list[AgentAdapter]:
    """Detect all agent tools installed on the system."""
    return [a for a in _ADAPTERS if a.is_installed()]


def list_known_agents() -> list[str]:
    """Return names of all known agents."""
    return [a.name for a in _ADAPTERS]
