"""GitHub artifact cleanup for publish E2E tests."""

from __future__ import annotations

import os
import subprocess


def cleanup_pr(repo: str, pr_number: int, token: str) -> None:
    """Close a PR in the test repo."""
    subprocess.run(
        ["gh", "pr", "close", str(pr_number), "--repo", repo, "--delete-branch"],
        env={**os.environ, "GH_TOKEN": token},
        capture_output=True, check=False,
    )


def cleanup_fork_branch(repo: str, branch: str, token: str) -> None:
    """Delete a branch from the fork."""
    subprocess.run(
        ["gh", "api", "-X", "DELETE",
         f"/repos/{repo}/git/refs/heads/{branch}"],
        env={**os.environ, "GH_TOKEN": token},
        capture_output=True, check=False,
    )


def cleanup_registry_file(repo: str, path: str, token: str) -> None:
    """Delete a registry file from the test repo (via API)."""
    result = subprocess.run(
        ["gh", "api", f"/repos/{repo}/contents/{path}", "--jq", ".sha"],
        env={**os.environ, "GH_TOKEN": token},
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        return
    sha = result.stdout.strip()
    subprocess.run(
        ["gh", "api", "-X", "DELETE", f"/repos/{repo}/contents/{path}",
         "-f", f"sha={sha}", "-f", "message=e2e cleanup"],
        env={**os.environ, "GH_TOKEN": token},
        capture_output=True, check=False,
    )
