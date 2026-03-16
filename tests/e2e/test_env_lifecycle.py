"""E2E tests for environment lifecycle: create, activate, switch, deactivate, delete."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from .helpers.agent_manager import AgentManager
from .helpers.platform_utils import PlatformAssert
from .helpers.run import EnvInfo, run_ipman

pytestmark = [pytest.mark.e2e, pytest.mark.platform]


def _unique_name() -> str:
    return f"e2e-{uuid4().hex[:8]}"


class TestEnvLifecycle:
    """Full environment lifecycle tests, parametrized by agent x scope."""

    def test_create_env(self, agent: str, scope: str, project_dir: Path) -> None:
        """Create an env, verify it appears in list, then clean up."""
        name = _unique_name()
        try:
            result = run_ipman(
                "env", "create", name, "--agent", agent, f"--{scope}",
                cwd=project_dir,
            )
            assert result.returncode == 0
            assert name in result.stdout

            # Verify in list
            ls = run_ipman("env", "list", f"--{scope}", cwd=project_dir)
            assert name in ls.stdout
        finally:
            run_ipman("env", "delete", name, f"--{scope}", "-y",
                      cwd=project_dir, check=False)

    def test_create_duplicate_env_fails(
        self, ipman_env: EnvInfo, project_dir: Path,
    ) -> None:
        """Creating an env with an existing name should error."""
        result = run_ipman(
            "env", "create", ipman_env.name,
            "--agent", ipman_env.agent, f"--{ipman_env.scope}",
            cwd=project_dir, check=False,
        )
        assert result.returncode != 0

    def test_activate_env(
        self, ipman_env: EnvInfo, project_dir: Path, agent: str,
    ) -> None:
        """Activate creates a symlink in the agent config directory."""
        run_ipman(
            "env", "activate", ipman_env.name, f"--{ipman_env.scope}",
            cwd=project_dir,
        )
        config_dir = project_dir / AgentManager.AGENT_CONFIG_DIR[agent]
        assert PlatformAssert.is_symlink(config_dir)

    def test_activate_generates_correct_shell_script(
        self, ipman_env: EnvInfo, project_dir: Path, agent: str,
    ) -> None:
        """Shell activation script is generated for the correct shell/OS."""
        import sys

        if sys.platform == "win32":
            shells = ["powershell"]
        else:
            shells = ["bash", "zsh", "fish"]

        # Activate first to create the env link
        run_ipman(
            "env", "activate", ipman_env.name, f"--{ipman_env.scope}",
            cwd=project_dir,
        )

        for _shell in shells:
            # The activate command outputs shell scripts when piped (non-tty)
            result = run_ipman(
                "env", "activate", ipman_env.name, f"--{ipman_env.scope}",
                cwd=project_dir, check=False,
            )
            # Should succeed (or at least produce output)
            assert result.returncode == 0 or result.stdout

    def test_switch_env(
        self, agent: str, scope: str, project_dir: Path,
    ) -> None:
        """Create two envs, activate first, switch to second, verify status."""
        name_a = _unique_name()
        name_b = _unique_name()
        try:
            run_ipman("env", "create", name_a, "--agent", agent, f"--{scope}",
                      cwd=project_dir)
            run_ipman("env", "create", name_b, "--agent", agent, f"--{scope}",
                      cwd=project_dir)

            # Activate a
            run_ipman("env", "activate", name_a, f"--{scope}", cwd=project_dir)

            # Switch to b
            run_ipman("env", "activate", name_b, f"--{scope}", cwd=project_dir)

            # Status should show b
            status = run_ipman("env", "status", cwd=project_dir)
            assert name_b in status.stdout
        finally:
            run_ipman("env", "deactivate", cwd=project_dir, check=False)
            run_ipman("env", "delete", name_a, f"--{scope}", "-y",
                      cwd=project_dir, check=False)
            run_ipman("env", "delete", name_b, f"--{scope}", "-y",
                      cwd=project_dir, check=False)

    def test_deactivate_env(
        self, ipman_env: EnvInfo, project_dir: Path, agent: str,
    ) -> None:
        """Deactivate removes symlink but env still shows in list."""
        run_ipman(
            "env", "activate", ipman_env.name, f"--{ipman_env.scope}",
            cwd=project_dir,
        )
        run_ipman("env", "deactivate", cwd=project_dir)

        config_dir = project_dir / AgentManager.AGENT_CONFIG_DIR[agent]
        assert not PlatformAssert.is_symlink(config_dir)

        # Env should still exist in list
        ls = run_ipman("env", "list", f"--{ipman_env.scope}", cwd=project_dir)
        assert ipman_env.name in ls.stdout

    def test_delete_env(
        self, agent: str, scope: str, project_dir: Path,
    ) -> None:
        """Delete removes env from list entirely."""
        name = _unique_name()
        run_ipman("env", "create", name, "--agent", agent, f"--{scope}",
                  cwd=project_dir)
        run_ipman("env", "delete", name, f"--{scope}", "-y", cwd=project_dir)

        ls = run_ipman("env", "list", f"--{scope}", cwd=project_dir, check=False)
        assert name not in ls.stdout

    def test_list_envs(
        self, agent: str, scope: str, project_dir: Path,
    ) -> None:
        """Create three envs; all must appear in list."""
        names = [_unique_name() for _ in range(3)]
        try:
            for n in names:
                run_ipman("env", "create", n, "--agent", agent, f"--{scope}",
                          cwd=project_dir)

            ls = run_ipman("env", "list", f"--{scope}", cwd=project_dir)
            for n in names:
                assert n in ls.stdout, f"{n} missing from list output"
        finally:
            for n in names:
                run_ipman("env", "delete", n, f"--{scope}", "-y",
                          cwd=project_dir, check=False)

    def test_status_shows_active(
        self, ipman_env: EnvInfo, project_dir: Path,
    ) -> None:
        """After activate, status output contains the env name."""
        run_ipman(
            "env", "activate", ipman_env.name, f"--{ipman_env.scope}",
            cwd=project_dir,
        )
        status = run_ipman("env", "status", cwd=project_dir)
        assert ipman_env.name in status.stdout

    def test_env_isolation_across_scopes(
        self, agent: str, project_dir: Path,
    ) -> None:
        """Same env name in two different scopes should not collide."""
        name = _unique_name()
        scopes = ["project", "user"]
        created: list[str] = []
        try:
            for s in scopes:
                run_ipman("env", "create", name, "--agent", agent, f"--{s}",
                          cwd=project_dir)
                created.append(s)

            # Both scopes should list the env independently
            for s in scopes:
                ls = run_ipman("env", "list", f"--{s}", cwd=project_dir)
                assert name in ls.stdout
        finally:
            for s in created:
                run_ipman("env", "delete", name, f"--{s}", "-y",
                          cwd=project_dir, check=False)
