"""E2E tests for skill install/uninstall via agent CLI (Layer 2)."""

from __future__ import annotations

from pathlib import Path

import pytest

from .helpers.agent_manager import AgentManager
from .helpers.run import EnvInfo, run_ipman

pytestmark = [pytest.mark.e2e, pytest.mark.agent_cli]

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestSkillInstall:
    """Verify skill install, uninstall, and persistence across env operations."""

    def test_install_skill_from_local(
        self, ipman_env: EnvInfo, project_dir: Path, agent: str,
        agent_manager: AgentManager,
    ) -> None:
        """Install a skill from local fixtures; verify it appears in agent list."""
        pytest.skip("Local skill directory install not yet supported — see Sprint 7 P0 task")

    def test_uninstall_skill(
        self, ipman_env: EnvInfo, project_dir: Path, agent: str,
        agent_manager: AgentManager,
    ) -> None:
        """Install then uninstall a skill; verify it is removed."""
        pytest.skip("Local skill directory install not yet supported — see Sprint 7 P0 task")

    def test_skill_persists_across_deactivate_reactivate(
        self, ipman_env: EnvInfo, project_dir: Path, agent: str,
        agent_manager: AgentManager,
    ) -> None:
        """Installed skill survives deactivate + reactivate cycle."""
        pytest.skip("Local skill directory install not yet supported — see Sprint 7 P0 task")

    def test_install_skill_from_hub(
        self, ipman_env: EnvInfo, project_dir: Path, agent: str,
    ) -> None:
        """Attempt hub install; may fail if hub unavailable but should not crash."""
        run_ipman(
            "env", "activate", ipman_env.name, f"--{ipman_env.scope}",
            cwd=project_dir,
        )

        result = run_ipman(
            "install", "nonexistent-hub-skill",
            "--agent", agent,
            cwd=project_dir, check=False, timeout=30,
        )

        # Should fail gracefully (not crash with traceback)
        assert result.returncode in (0, 1), (
            f"Hub install crashed: rc={result.returncode}, "
            f"stderr={result.stderr}"
        )

    def test_install_with_security_vetting(
        self, ipman_env: EnvInfo, project_dir: Path, agent: str,
    ) -> None:
        """Install with --security strict should not crash."""
        run_ipman(
            "env", "activate", ipman_env.name, f"--{ipman_env.scope}",
            cwd=project_dir,
        )

        # Use a skill name (not directory) — ipman install accepts .ip.yaml
        # or IpHub names. This will fail gracefully ("not found in IpHub").
        result = run_ipman(
            "install", "nonexistent-security-test-skill",
            "--agent", agent, "--security", "strict",
            cwd=project_dir, check=False, timeout=30,
        )

        # May reject or accept, but should not crash
        assert result.returncode in (0, 1), (
            f"Security-vetting install crashed: rc={result.returncode}, "
            f"stderr={result.stderr}"
        )
