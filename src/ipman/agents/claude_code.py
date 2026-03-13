"""Claude Code agent adapter."""

from __future__ import annotations

import shutil
from pathlib import Path

from ipman.agents.base import AgentAdapter


class ClaudeCodeAdapter(AgentAdapter):
    """Adapter for Claude Code."""

    @property
    def name(self) -> str:
        return "claude-code"

    @property
    def display_name(self) -> str:
        return "Claude Code"

    @property
    def config_dir_name(self) -> str:
        return ".claude"

    def is_installed(self) -> bool:
        return shutil.which("claude") is not None

    def init_env_dir(self, env_path: Path) -> None:
        """Create Claude Code environment structure."""
        skills_dir = env_path / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)
