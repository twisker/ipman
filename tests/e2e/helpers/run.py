"""CLI invocation helper and shared dataclasses for E2E tests."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class EnvInfo:
    """Tracks a created ipman environment for cleanup."""
    name: str
    agent: str
    scope: str
    project: Path


@dataclass
class SessionResult:
    """Result of an agent session invocation."""
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float


@dataclass
class GitHubAuth:
    """GitHub authentication context for publish tests."""
    identity: str
    token: str


@dataclass
class PublishContext:
    """Tracks GitHub artifacts for cleanup after publish tests."""
    skill_name: str
    repo: str = ""
    token: str = ""
    created_prs: list[int] = field(default_factory=list)
    created_branches: list[str] = field(default_factory=list)
    created_registry_files: list[str] = field(default_factory=list)


def run_ipman(
    *args: str,
    cwd: Path | None = None,
    check: bool = True,
    timeout: int = 30,
) -> subprocess.CompletedProcess[str]:
    """Invoke ipman CLI via uv run. Returns CompletedProcess."""
    cmd = ["uv", "run", "ipman", *args]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=cwd,
        check=check,
        timeout=timeout,
    )
