"""Agent lifecycle manager for E2E tests."""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from typing import ClassVar

from ipman.agents.base import SkillInfo
from ipman.agents.registry import get_adapter

from .run import SessionResult


class AgentManager:
    """Test helper wrapping production AgentAdapter + session management."""

    SESSION_COMMANDS: ClassVar[dict[str, dict[str, object]]] = {
        "claude-code": {"cmd": ["claude", "--print"], "prompt_arg": "positional"},
        "openclaw":    {"cmd": ["openclaw", "run"],   "prompt_arg": "positional"},
    }

    AGENT_CONFIG_DIR: ClassVar[dict[str, str]] = {
        "claude-code": ".claude",
        "openclaw": ".openclaw",
    }

    def __init__(self, agent_name: str, project_dir: Path) -> None:
        self.agent_name = agent_name
        self.project_dir = project_dir
        self._adapter = get_adapter(agent_name)

    @staticmethod
    def is_installed(name: str) -> bool:
        """Check if agent CLI is available on PATH."""
        try:
            return get_adapter(name).is_installed()
        except ValueError:
            return False

    def install_skill(self, name: str, **kwargs: str | None) -> bool:
        """Install a skill via agent CLI. Returns True on success."""
        result = self._adapter.install_skill(name, **kwargs)
        return result.returncode == 0

    def uninstall_skill(self, name: str) -> bool:
        """Uninstall a skill via agent CLI. Returns True on success."""
        result = self._adapter.uninstall_skill(name)
        return result.returncode == 0

    def list_skills(self) -> list[SkillInfo]:
        """List installed skills via agent CLI."""
        return self._adapter.list_skills()

    @property
    def config_dir_name(self) -> str:
        """Agent config directory name (e.g. '.claude')."""
        return self.AGENT_CONFIG_DIR[self.agent_name]

    def start_session(
        self,
        prompt: str = "Reply with exactly: OK",
        timeout: int = 60,
    ) -> SessionResult:
        """Start a minimal, controlled agent session."""
        spec = self.SESSION_COMMANDS[self.agent_name]
        cmd_parts: list[str] = list(spec["cmd"])  # type: ignore[arg-type]
        cmd = [*cmd_parts, prompt]

        env = {**os.environ}
        if self.agent_name == "claude-code":
            key = os.environ.get("ANTHROPIC_API_KEY", "")
            if not key:
                return SessionResult(
                    exit_code=-2, stdout="",
                    stderr="ANTHROPIC_API_KEY not set",
                    duration_seconds=0,
                )
            env["ANTHROPIC_API_KEY"] = key

        start = time.monotonic()
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=timeout, cwd=self.project_dir, env=env,
            )
            return SessionResult(
                exit_code=result.returncode, stdout=result.stdout,
                stderr=result.stderr,
                duration_seconds=time.monotonic() - start,
            )
        except subprocess.TimeoutExpired as e:
            return SessionResult(
                exit_code=-1,
                stdout=e.stdout or "" if isinstance(e.stdout, str) else "",
                stderr=f"TIMEOUT after {timeout}s",
                duration_seconds=timeout,
            )
