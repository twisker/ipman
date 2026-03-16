"""E2E tests for symlink/junction integrity across platforms."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from .helpers.agent_manager import AgentManager
from .helpers.platform_utils import PlatformAssert
from .helpers.run import EnvInfo, run_ipman

pytestmark = [pytest.mark.e2e, pytest.mark.platform, pytest.mark.symlink]


class TestSymlinkIntegrity:
    """Verify symlinks survive filesystem operations and edge cases."""

    def test_symlink_created_correctly(
        self, ipman_env: EnvInfo, project_dir: Path, agent: str,
    ) -> None:
        """Activating an env creates a valid symlink."""
        run_ipman(
            "env", "activate", ipman_env.name, f"--{ipman_env.scope}",
            cwd=project_dir,
        )
        config_dir = project_dir / AgentManager.AGENT_CONFIG_DIR[agent]
        assert PlatformAssert.is_symlink(config_dir)

    def test_symlink_target_points_to_env_storage(
        self, ipman_env: EnvInfo, project_dir: Path, agent: str,
    ) -> None:
        """Symlink target path contains the environment name."""
        run_ipman(
            "env", "activate", ipman_env.name, f"--{ipman_env.scope}",
            cwd=project_dir,
        )
        config_dir = project_dir / AgentManager.AGENT_CONFIG_DIR[agent]
        target = PlatformAssert.symlink_target(config_dir)
        assert ipman_env.name in str(target), (
            f"Expected env name '{ipman_env.name}' in symlink target '{target}'"
        )

    def test_symlink_survives_file_write(
        self, ipman_env: EnvInfo, project_dir: Path, agent: str,
    ) -> None:
        """Writing a file inside the symlinked dir preserves the symlink."""
        run_ipman(
            "env", "activate", ipman_env.name, f"--{ipman_env.scope}",
            cwd=project_dir,
        )
        config_dir = project_dir / AgentManager.AGENT_CONFIG_DIR[agent]

        # Write a file through the symlink
        test_file = config_dir / "test_artifact.txt"
        test_file.write_text("e2e symlink write test")

        assert test_file.read_text() == "e2e symlink write test"
        assert PlatformAssert.is_symlink(config_dir)

    def test_symlink_survives_nested_dir_creation(
        self, ipman_env: EnvInfo, project_dir: Path, agent: str,
    ) -> None:
        """Creating nested subdirectories inside the symlink preserves it."""
        run_ipman(
            "env", "activate", ipman_env.name, f"--{ipman_env.scope}",
            cwd=project_dir,
        )
        config_dir = project_dir / AgentManager.AGENT_CONFIG_DIR[agent]

        nested = config_dir / "subdir" / "deep" / "nested"
        nested.mkdir(parents=True, exist_ok=True)
        (nested / "marker.txt").write_text("deep")

        assert (nested / "marker.txt").read_text() == "deep"
        assert PlatformAssert.is_symlink(config_dir)

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-only junction test")
    def test_junction_on_windows(
        self, ipman_env: EnvInfo, project_dir: Path, agent: str,
    ) -> None:
        """On Windows, verify the link is a junction (directory symlink)."""
        import os

        run_ipman(
            "env", "activate", ipman_env.name, f"--{ipman_env.scope}",
            cwd=project_dir,
        )
        config_dir = project_dir / AgentManager.AGENT_CONFIG_DIR[agent]

        # On Windows, os.readlink works for junctions
        assert config_dir.is_dir()
        target = os.readlink(config_dir)
        assert ipman_env.name in target

    def test_symlink_after_rapid_toggle(
        self, ipman_env: EnvInfo, project_dir: Path, agent: str,
    ) -> None:
        """Rapid activate/deactivate cycles (3x) leave symlink in correct state."""
        for _ in range(3):
            run_ipman(
                "env", "activate", ipman_env.name, f"--{ipman_env.scope}",
                cwd=project_dir,
            )
            run_ipman("env", "deactivate", cwd=project_dir)

        # Final activate — should still work
        run_ipman(
            "env", "activate", ipman_env.name, f"--{ipman_env.scope}",
            cwd=project_dir,
        )
        config_dir = project_dir / AgentManager.AGENT_CONFIG_DIR[agent]
        assert PlatformAssert.is_symlink(config_dir)

    def test_real_dir_replaced_by_symlink(
        self, ipman_env: EnvInfo, project_dir: Path, agent: str,
    ) -> None:
        """Existing real dir + --inherit should become a symlink with content preserved."""
        config_dir = project_dir / AgentManager.AGENT_CONFIG_DIR[agent]

        # Ensure real dir exists with content
        config_dir.mkdir(exist_ok=True)
        marker = config_dir / "pre_existing.txt"
        marker.write_text("should survive")

        # Create a new env with --inherit to migrate the content
        from uuid import uuid4

        inherit_name = f"e2e-inherit-{uuid4().hex[:8]}"
        try:
            run_ipman(
                "env", "create", inherit_name, "--agent", agent,
                f"--{ipman_env.scope}", "--inherit",
                cwd=project_dir,
            )
            run_ipman(
                "env", "activate", inherit_name, f"--{ipman_env.scope}",
                cwd=project_dir,
            )

            # Config dir should now be a symlink
            assert PlatformAssert.is_symlink(config_dir)

            # Content should be preserved
            assert (config_dir / "pre_existing.txt").read_text() == "should survive"
        finally:
            run_ipman("env", "deactivate", cwd=project_dir, check=False)
            run_ipman(
                "env", "delete", inherit_name, f"--{ipman_env.scope}", "-y",
                cwd=project_dir, check=False,
            )

    def test_broken_symlink_recovery(
        self, ipman_env: EnvInfo, project_dir: Path, agent: str,
    ) -> None:
        """After deactivate, env list should not crash (no broken symlinks)."""
        run_ipman(
            "env", "activate", ipman_env.name, f"--{ipman_env.scope}",
            cwd=project_dir,
        )
        run_ipman("env", "deactivate", cwd=project_dir)

        # List should work without errors
        result = run_ipman(
            "env", "list", f"--{ipman_env.scope}", cwd=project_dir,
        )
        assert result.returncode == 0
