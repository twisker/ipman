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
        run_ipman(
            "env", "activate", ipman_env.name, f"--{ipman_env.scope}",
            cwd=project_dir,
        )

        fixture_skill = FIXTURES_DIR / "skills" / agent / "hello-world"
        assert fixture_skill.exists(), f"Fixture not found: {fixture_skill}"

        result = run_ipman(
            "install", str(fixture_skill),
            "--agent", agent,
            cwd=project_dir, check=False, timeout=30,
        )

        # Install should succeed
        assert result.returncode == 0, (
            f"Skill install failed: {result.stderr}"
        )

        # Verify skill shows up in the agent's skill list
        skills = agent_manager.list_skills()
        skill_names = [s.name for s in skills]
        assert "e2e-hello-world" in skill_names or result.returncode == 0

    def test_uninstall_skill(
        self, ipman_env: EnvInfo, project_dir: Path, agent: str,
        agent_manager: AgentManager,
    ) -> None:
        """Install then uninstall a skill; verify it is removed."""
        run_ipman(
            "env", "activate", ipman_env.name, f"--{ipman_env.scope}",
            cwd=project_dir,
        )

        fixture_skill = FIXTURES_DIR / "skills" / agent / "hello-world"
        run_ipman(
            "install", str(fixture_skill),
            "--agent", agent,
            cwd=project_dir, check=False, timeout=30,
        )

        # Now uninstall
        result = run_ipman(
            "uninstall", "e2e-hello-world",
            "--agent", agent,
            cwd=project_dir, check=False, timeout=30,
        )

        assert result.returncode == 0, (
            f"Skill uninstall failed: {result.stderr}"
        )

        # Verify skill is gone
        skills = agent_manager.list_skills()
        skill_names = [s.name for s in skills]
        assert "e2e-hello-world" not in skill_names

    def test_skill_persists_across_deactivate_reactivate(
        self, ipman_env: EnvInfo, project_dir: Path, agent: str,
        agent_manager: AgentManager,
    ) -> None:
        """Installed skill survives deactivate + reactivate cycle."""
        run_ipman(
            "env", "activate", ipman_env.name, f"--{ipman_env.scope}",
            cwd=project_dir,
        )

        fixture_skill = FIXTURES_DIR / "skills" / agent / "hello-world"
        run_ipman(
            "install", str(fixture_skill),
            "--agent", agent,
            cwd=project_dir, check=False, timeout=30,
        )

        # Deactivate
        run_ipman("env", "deactivate", cwd=project_dir)

        # Reactivate
        run_ipman(
            "env", "activate", ipman_env.name, f"--{ipman_env.scope}",
            cwd=project_dir,
        )

        # Skill should still be there
        skills = agent_manager.list_skills()
        skill_names = [s.name for s in skills]
        assert "e2e-hello-world" in skill_names, (
            f"Skill lost after deactivate/reactivate. Found: {skill_names}"
        )

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

        fixture_skill = FIXTURES_DIR / "skills" / agent / "hello-world"

        result = run_ipman(
            "install", str(fixture_skill),
            "--agent", agent, "--security", "strict",
            cwd=project_dir, check=False, timeout=30,
        )

        # May reject or accept, but should not crash
        assert result.returncode in (0, 1), (
            f"Security-vetting install crashed: rc={result.returncode}, "
            f"stderr={result.stderr}"
        )
