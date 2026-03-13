"""Base class for Agent tool adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class AgentAdapter(ABC):
    """Base adapter for an Agent tool (e.g. Claude Code, OpenClaw).

    Each adapter tells IpMan:
    - What the agent's config directory is called
    - How to detect if the agent is installed
    - How to initialize a fresh environment directory for the agent
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Agent identifier, e.g. 'claude-code'."""

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name, e.g. 'Claude Code'."""

    @property
    @abstractmethod
    def config_dir_name(self) -> str:
        """Name of the agent's config directory, e.g. '.claude'."""

    @abstractmethod
    def is_installed(self) -> bool:
        """Check if this agent tool is installed on the system."""

    @abstractmethod
    def init_env_dir(self, env_path: Path) -> None:
        """Initialize a fresh environment directory with agent-specific structure.

        For example, Claude Code needs a skills/ directory.
        """

    def detect_in_project(self, project_path: Path) -> bool:
        """Check if this agent is used in the given project directory."""
        return (project_path / self.config_dir_name).exists()
