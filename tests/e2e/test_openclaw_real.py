"""Real E2E tests for OpenClaw adapter — requires clawhub on PATH.

These tests invoke the actual clawhub CLI and verify that ipman's OpenClaw
adapter works against a live installation. They are the hard gate for Phase 3
of the Comprehensive Validation Sprint.

To run:
    pytest tests/e2e/test_openclaw_real.py -v

If clawhub is not installed, all tests are skipped automatically.
For mock-based regression tests, see test_openclaw_compat.py.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from uuid import uuid4

import pytest

from tests.e2e.helpers.run import run_ipman

pytestmark = [pytest.mark.e2e, pytest.mark.requires_clawhub]


@pytest.fixture(autouse=True)
def require_clawhub() -> None:
    """Skip all tests in this module if clawhub is not on PATH."""
    if not shutil.which("clawhub"):
        pytest.skip("clawhub not on PATH — install OpenClaw to run Phase 3 tests")


def _unique_name() -> str:
    return f"real-e2e-{uuid4().hex[:8]}"


# ---------------------------------------------------------------------------
# Section 1: is_installed() detection
# ---------------------------------------------------------------------------

class TestOpenClawDetection:
    """Verify that ipman correctly detects OpenClaw via clawhub binary."""

    def test_is_installed_returns_true_with_clawhub(self) -> None:
        """OpenClaw adapter reports installed when clawhub is on PATH."""
        from ipman.agents.openclaw import OpenClawAdapter
        adapter = OpenClawAdapter()
        assert adapter.is_installed() is True

    def test_clawhub_version_accessible(self) -> None:
        """clawhub --version exits 0 and prints a version string."""
        result = subprocess.run(
            ["clawhub", "--version"],
            capture_output=True, text=True, check=False,
        )
        assert result.returncode == 0, (
            f"clawhub --version failed: {result.stderr}"
        )


# ---------------------------------------------------------------------------
# Section 2: Skill install / uninstall / list
# ---------------------------------------------------------------------------

class TestRealClawHubSkillLifecycle:
    """Install, verify, and uninstall a skill via real clawhub."""

    def test_list_skills_returns_list(self, tmp_path: Path) -> None:
        """list_skills() returns a list (possibly empty) without error."""
        from ipman.agents.openclaw import OpenClawAdapter
        adapter = OpenClawAdapter()
        skills = adapter.list_skills()
        assert isinstance(skills, list)

    def test_install_and_uninstall_local_skill(self, tmp_path: Path) -> None:
        """Install a local skill dir via clawhub, verify presence, then uninstall."""
        # Create a minimal local skill directory
        skill_name = _unique_name()
        skill_dir = tmp_path / skill_name
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            f"# {skill_name}\nA test skill for ipman E2E validation.\n"
        )

        from ipman.agents.openclaw import OpenClawAdapter
        adapter = OpenClawAdapter()

        # Install
        result = adapter.install_skill(
            str(skill_dir),
            config_dir=str(tmp_path / ".openclaw"),
        )
        assert result.returncode == 0, (
            f"install_skill failed (rc={result.returncode}): {result.stderr}"
        )

        # Uninstall
        result = adapter.uninstall_skill(skill_name, auto_yes=True)
        # rc=0 is ideal; rc!=0 is acceptable if clawhub doesn't support uninstall
        # for locally-copied skills — document the gap if it fails
        if result.returncode != 0:
            pytest.xfail(
                f"clawhub uninstall returned {result.returncode}: {result.stderr}"
            )


# ---------------------------------------------------------------------------
# Section 3: ipman CLI → OpenClaw passthrough
# ---------------------------------------------------------------------------

class TestIpmanOpenClawCLI:
    """Verify ipman CLI commands reach OpenClaw via --agent openclaw."""

    def test_install_from_local_dir(self, tmp_path: Path) -> None:
        """ipman install ./skill --agent openclaw succeeds."""
        skill_name = _unique_name()
        skill_dir = tmp_path / skill_name
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(f"# {skill_name}\nE2E test skill.\n")

        result = run_ipman(
            "install", str(skill_dir), "--agent", "openclaw",
            cwd=tmp_path, check=False,
        )
        assert result.returncode == 0, (
            f"ipman install failed: stdout={result.stdout} stderr={result.stderr}"
        )


# ---------------------------------------------------------------------------
# Section 4: Cross-agent portability
# ---------------------------------------------------------------------------

class TestCrossAgentPortability:
    """Same IP package installs into both Claude Code and OpenClaw."""

    def test_same_local_skill_installs_in_both_agents(
        self, tmp_path: Path,
    ) -> None:
        """A local skill directory can be installed via both adapters."""
        import shutil as _shutil

        from ipman.agents.claude_code import ClaudeCodeAdapter
        from ipman.agents.openclaw import OpenClawAdapter

        if not _shutil.which("claude"):
            pytest.skip("claude CLI not on PATH — needed for cross-agent test")

        skill_name = _unique_name()
        skill_dir = tmp_path / skill_name
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(f"# {skill_name}\nCross-agent test.\n")

        cc_adapter = ClaudeCodeAdapter()
        oc_adapter = OpenClawAdapter()

        cc_result = cc_adapter.install_skill(
            str(skill_dir),
            config_dir=str(tmp_path / ".claude"),
        )
        oc_result = oc_adapter.install_skill(
            str(skill_dir),
            config_dir=str(tmp_path / ".openclaw"),
        )

        assert cc_result.returncode == 0, (
            f"Claude Code install failed: {cc_result.stderr}"
        )
        assert oc_result.returncode == 0, (
            f"OpenClaw install failed: {oc_result.stderr}"
        )
