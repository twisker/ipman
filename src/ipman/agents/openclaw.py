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
        self, name: str, *, auto_yes: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        """Uninstall a skill via ``clawhub uninstall``."""
        args = ["clawhub", "uninstall", name]
        if auto_yes:
            args.append("--yes")
        return self._run_cli(args)

    def list_skills(self, workdir: Path | None = None) -> list[SkillInfo]:
        """List installed skills with 3-strategy fallback.

        1. Try ``clawhub list --json``
        2. Fall back to parsing ``clawhub list`` plain text
        3. Fall back to reading ``.clawhub/lock.json``
        """
        # Strategy 1: try --json
        result = self._run_cli(["clawhub", "list", "--json"])
        if result.returncode == 0:
            try:
                skills = json.loads(result.stdout)
                return [
                    SkillInfo(
                        name=s.get("name", ""),
                        version=s.get("version", ""),
                    )
                    for s in skills
                ]
            except (json.JSONDecodeError, TypeError):
                pass

        # Strategy 2: parse plain text
        result_plain = self._run_cli(["clawhub", "list"])
        if result_plain.returncode == 0 and result_plain.stdout.strip():
            return self._parse_plain_list(result_plain.stdout)

        # Strategy 3: read lockfile
        return self._read_lockfile(workdir or Path.cwd())

    @staticmethod
    def _parse_plain_list(output: str) -> list[SkillInfo]:
        """Parse plain text output from ``clawhub list``."""
        skills: list[SkillInfo] = []
        for line in output.strip().splitlines():
            parts = line.split()
            if not parts:
                continue
            name = parts[0]
            version = parts[1] if len(parts) > 1 else ""
            # Skip header/separator lines
            if name.startswith("-") or name.startswith("="):
                continue
            skills.append(SkillInfo(name=name, version=version))
        return skills

    @staticmethod
    def _read_lockfile(workdir: Path) -> list[SkillInfo]:
        """Read skills from .clawhub/lock.json as last resort."""
        lock_file = workdir / ".clawhub" / "lock.json"
        if not lock_file.exists():
            return []
        try:
            data = json.loads(lock_file.read_text(encoding="utf-8"))
            skills_data = data.get("skills", {})
            return [
                SkillInfo(name=name, version=info.get("version", ""))
                for name, info in skills_data.items()
            ]
        except (json.JSONDecodeError, TypeError, AttributeError):
            return []
