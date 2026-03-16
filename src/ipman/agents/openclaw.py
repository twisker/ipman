"""OpenClaw agent adapter."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from ipman.agents.base import AgentAdapter, SkillInfo


class OpenClawAdapter(AgentAdapter):
    """Adapter for OpenClaw.

    Skill operations delegate to ``clawhub`` CLI commands.
    """

    @property
    def name(self) -> str:
        return "openclaw"

    @property
    def display_name(self) -> str:
        return "OpenClaw"

    @property
    def config_dir_name(self) -> str:
        return ".openclaw"

    def is_installed(self) -> bool:
        return shutil.which("openclaw") is not None

    def init_env_dir(self, env_path: Path) -> None:
        """Create OpenClaw environment structure."""
        skills_dir = env_path / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)

    def install_skill(
        self, name: str, **kwargs: str | None,
    ) -> subprocess.CompletedProcess[str]:
        """Install a skill.

        If *name* is an existing directory, copy it into the agent's
        skills/ dir. Otherwise delegate to ``clawhub install``.
        """
        path = Path(name)
        if path.exists() and path.is_dir():
            config_dir = kwargs.get("config_dir")
            if config_dir:
                dest = Path(str(config_dir)) / "skills" / path.name
            else:
                dest = Path.cwd() / ".openclaw" / "skills" / path.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(path, dest, dirs_exist_ok=True)
            return subprocess.CompletedProcess(
                args=[], returncode=0,
                stdout=f"Copied to {dest}\n", stderr="",
            )
        args = ["clawhub", "install", name]
        hub = kwargs.get("hub")
        if hub:
            args.extend(["--hub", str(hub)])
        return self._run_cli(args)

    def uninstall_skill(
        self, name: str,
    ) -> subprocess.CompletedProcess[str]:
        """Uninstall a skill via ``clawhub uninstall``."""
        return self._run_cli(
            ["clawhub", "uninstall", name],
        )

    def list_skills(self) -> list[SkillInfo]:
        """List installed skills via ``clawhub list --json``."""
        result = self._run_cli(
            ["clawhub", "list", "--json"],
        )
        if result.returncode != 0:
            return []
        try:
            skills = json.loads(result.stdout)
        except (json.JSONDecodeError, TypeError):
            return []
        return [
            SkillInfo(
                name=s.get("name", ""),
                version=s.get("version", ""),
            )
            for s in skills
        ]
