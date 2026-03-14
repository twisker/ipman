"""Claude Code agent adapter."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from ipman.agents.base import AgentAdapter, SkillInfo


class ClaudeCodeAdapter(AgentAdapter):
    """Adapter for Claude Code.

    Skill operations delegate to `claude plugin` CLI commands.
    """

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

    def install_skill(
        self, name: str, **kwargs: str | None,
    ) -> subprocess.CompletedProcess[str]:
        """Install a plugin via ``claude plugin install``."""
        args = ["claude", "plugin", "install", name]
        scope = kwargs.get("scope")
        if scope:
            args.extend(["-s", scope])
        return self._run_cli(args)

    def uninstall_skill(
        self, name: str,
    ) -> subprocess.CompletedProcess[str]:
        """Uninstall a plugin via ``claude plugin uninstall``."""
        return self._run_cli(
            ["claude", "plugin", "uninstall", name],
        )

    def list_skills(self) -> list[SkillInfo]:
        """List installed plugins via ``claude plugin list --json``."""
        result = self._run_cli(
            ["claude", "plugin", "list", "--json"],
        )
        if result.returncode != 0:
            return []
        try:
            plugins = json.loads(result.stdout)
        except (json.JSONDecodeError, TypeError):
            return []
        return [
            SkillInfo(
                name=p.get("id", p.get("name", "")),
                version=p.get("version", ""),
                enabled=p.get("enabled", True),
            )
            for p in plugins
        ]
