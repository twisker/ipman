"""Base class for Agent tool adapters."""

from __future__ import annotations

import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SkillInfo:
    """Structured info about an installed skill."""

    name: str
    version: str = ""
    enabled: bool = True
    source: str = ""


class AgentAdapter(ABC):
    """Base adapter for an Agent tool (e.g. Claude Code, OpenClaw).

    Each adapter tells IpMan:
    - What the agent's config directory is called
    - How to detect if the agent is installed
    - How to initialize a fresh environment directory for the agent
    - How to install/uninstall/list skills via agent CLI commands
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
        """Initialize a fresh environment directory."""

    def detect_in_project(self, project_path: Path) -> bool:
        """Check if this agent is used in the given project directory."""
        return (project_path / self.config_dir_name).exists()

    # --- Skill CLI delegation (Sprint 2) ---

    @abstractmethod
    def install_skill(
        self, name: str, **kwargs: str | None,
    ) -> subprocess.CompletedProcess[str]:
        """Install a skill via agent's native CLI command."""

    @abstractmethod
    def uninstall_skill(
        self, name: str,
    ) -> subprocess.CompletedProcess[str]:
        """Uninstall a skill via agent's native CLI command."""

    @abstractmethod
    def list_skills(self) -> list[SkillInfo]:
        """List installed skills via agent's native CLI command."""

    def _run_cli(
        self, args: list[str],
    ) -> subprocess.CompletedProcess[str]:
        """Run a CLI command and capture output."""
        return subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=False,
        )
