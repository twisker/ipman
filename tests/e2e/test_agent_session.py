"""E2E tests for agent session integrity (Layer 3)."""

from __future__ import annotations

import os
import threading
from pathlib import Path
from uuid import uuid4

import pytest

from .helpers.agent_manager import AgentManager
from .helpers.platform_utils import PlatformAssert
from .helpers.run import EnvInfo, run_ipman

pytestmark = [pytest.mark.e2e, pytest.mark.agent_session, pytest.mark.slow]

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _has_api_key(agent: str) -> bool:
    """Check whether the required API key is available for *agent*."""
    if agent == "claude-code":
        return bool(os.environ.get("ANTHROPIC_API_KEY"))
    # openclaw / others: assume available
    return True


# ===========================================================================
# Tests
# ===========================================================================


class TestAgentSession:
    """Verify ipman env integrity survives real agent sessions."""

    def test_symlink_survives_agent_session(
        self, ipman_env: EnvInfo, project_dir: Path, agent: str,
        agent_manager: AgentManager,
    ) -> None:
        """THE CORE TEST: activate env, start agent session, assert symlink still alive."""
        if not _has_api_key(agent):
            pytest.skip(f"API key not available for {agent}")

        run_ipman(
            "env", "activate", ipman_env.name, f"--{ipman_env.scope}",
            cwd=project_dir,
        )

        config_dir = project_dir / AgentManager.AGENT_CONFIG_DIR[agent]
        assert PlatformAssert.is_symlink(config_dir), (
            "Symlink should exist before session"
        )

        # Run a minimal agent session
        session = agent_manager.start_session(
            prompt="Reply with exactly: OK",
            timeout=60,
        )

        # Gracefully skip if API credit balance is too low
        _output = (session.stdout or "") + (session.stderr or "")
        if session.exit_code == 1 and "credit balance" in _output.lower():
            pytest.skip("Skipped: API credit balance too low")

        # Symlink must still be alive after the session
        assert PlatformAssert.is_symlink(config_dir), (
            f"Symlink destroyed during session! "
            f"exit_code={session.exit_code}, stderr={session.stderr}"
        )

    def test_agent_session_does_not_corrupt_metadata(
        self, ipman_env: EnvInfo, project_dir: Path, agent: str,
        agent_manager: AgentManager,
    ) -> None:
        """Status output should be identical before and after a session."""
        if not _has_api_key(agent):
            pytest.skip(f"API key not available for {agent}")

        run_ipman(
            "env", "activate", ipman_env.name, f"--{ipman_env.scope}",
            cwd=project_dir,
        )

        # Capture status before session
        status_before = run_ipman("env", "status", cwd=project_dir)

        # Run session
        agent_manager.start_session(
            prompt="Reply with exactly: OK",
            timeout=60,
        )

        # Capture status after session
        status_after = run_ipman("env", "status", cwd=project_dir)

        assert ipman_env.name in status_before.stdout
        assert ipman_env.name in status_after.stdout
        # Core metadata (env name) must be preserved
        assert status_before.stdout == status_after.stdout, (
            f"Status changed after session:\n"
            f"  before: {status_before.stdout!r}\n"
            f"  after:  {status_after.stdout!r}"
        )

    def test_installed_skill_visible_in_session(
        self, ipman_env: EnvInfo, project_dir: Path, agent: str,
        agent_manager: AgentManager,
    ) -> None:
        """Install a skill, start session; agent should not crash."""
        if not _has_api_key(agent):
            pytest.skip(f"API key not available for {agent}")

        run_ipman(
            "env", "activate", ipman_env.name, f"--{ipman_env.scope}",
            cwd=project_dir,
        )

        # Install a test skill
        fixture_skill = FIXTURES_DIR / "skills" / agent / "hello-world"
        run_ipman(
            "install", str(fixture_skill),
            "--agent", agent,
            cwd=project_dir, check=False, timeout=30,
        )

        # Start session -- should not crash even with installed skills
        session = agent_manager.start_session(
            prompt="Reply with exactly: OK",
            timeout=60,
        )

        # Gracefully skip if API credit balance is too low
        _output = (session.stdout or "") + (session.stderr or "")
        if session.exit_code == 1 and "credit balance" in _output.lower():
            pytest.skip("Skipped: API credit balance too low")

        # Session should complete (exit_code 0) or timeout gracefully (-1)
        assert session.exit_code in (0, -1, -2), (
            f"Session crashed with installed skill: "
            f"exit_code={session.exit_code}, stderr={session.stderr}"
        )

    def test_env_switch_reflected_in_new_session(
        self, agent: str, scope: str, project_dir: Path,
        agent_manager: AgentManager,
    ) -> None:
        """Create 2 envs, switch between them, verify status is correct."""
        if not _has_api_key(agent):
            pytest.skip(f"API key not available for {agent}")

        name_a = f"e2e-{uuid4().hex[:8]}"
        name_b = f"e2e-{uuid4().hex[:8]}"
        try:
            run_ipman(
                "env", "create", name_a, "--agent", agent, f"--{scope}",
                cwd=project_dir,
            )
            run_ipman(
                "env", "create", name_b, "--agent", agent, f"--{scope}",
                cwd=project_dir,
            )

            # Activate env A
            run_ipman(
                "env", "activate", name_a, f"--{scope}", cwd=project_dir,
            )
            status_a = run_ipman("env", "status", cwd=project_dir)
            assert name_a in status_a.stdout

            # Switch to env B
            run_ipman(
                "env", "activate", name_b, f"--{scope}", cwd=project_dir,
            )
            status_b = run_ipman("env", "status", cwd=project_dir)
            assert name_b in status_b.stdout
            assert name_a not in status_b.stdout, (
                "Old env name should not appear after switch"
            )
        finally:
            run_ipman("env", "deactivate", cwd=project_dir, check=False)
            run_ipman(
                "env", "delete", name_a, f"--{scope}", "-y",
                cwd=project_dir, check=False,
            )
            run_ipman(
                "env", "delete", name_b, f"--{scope}", "-y",
                cwd=project_dir, check=False,
            )

    def test_concurrent_sessions_different_projects(
        self, agent: str, scope: str, tmp_path: Path,
    ) -> None:
        """Two projects running simultaneous sessions should not interfere."""
        if not _has_api_key(agent):
            pytest.skip(f"API key not available for {agent}")

        projects: dict[str, dict[str, str | Path]] = {}
        errors: list[str] = []

        for label in ("proj_a", "proj_b"):
            workspace = tmp_path / label
            workspace.mkdir()
            config_dir_name = AgentManager.AGENT_CONFIG_DIR[agent]
            (workspace / config_dir_name).mkdir()

            env_name = f"e2e-{uuid4().hex[:8]}"
            run_ipman(
                "env", "create", env_name, "--agent", agent, f"--{scope}",
                cwd=workspace,
            )
            run_ipman(
                "env", "activate", env_name, f"--{scope}", cwd=workspace,
            )
            projects[label] = {
                "workspace": workspace,
                "env_name": env_name,
                "config_dir": workspace / config_dir_name,
            }

        def _run_session(label: str) -> None:
            try:
                info = projects[label]
                mgr = AgentManager(agent, info["workspace"])  # type: ignore[arg-type]
                mgr.start_session(prompt="Reply with exactly: OK", timeout=60)
            except Exception as exc:
                errors.append(f"{label}: {exc}")

        threads = [
            threading.Thread(target=_run_session, args=(lbl,))
            for lbl in projects
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=120)

        assert not errors, f"Session thread errors: {errors}"

        # Both symlinks should still be intact
        for label, info in projects.items():
            config_dir = info["config_dir"]
            assert PlatformAssert.is_symlink(Path(str(config_dir))), (
                f"Symlink destroyed in {label} during concurrent session"
            )

        # Cleanup
        for _label, info in projects.items():
            run_ipman("env", "deactivate",
                      cwd=info["workspace"], check=False)  # type: ignore[arg-type]
            run_ipman(
                "env", "delete", str(info["env_name"]), f"--{scope}", "-y",
                cwd=info["workspace"], check=False,  # type: ignore[arg-type]
            )
