"""E2E tests for init-order independence: ipman-first vs agent-first."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from .helpers.agent_manager import AgentManager
from .helpers.platform_utils import PlatformAssert
from .helpers.run import run_ipman

pytestmark = [pytest.mark.e2e, pytest.mark.platform]


def _unique_name() -> str:
    return f"e2e-{uuid4().hex[:8]}"


class TestInitOrder:
    """Verify ipman works regardless of whether it or the agent was set up first."""

    @pytest.fixture(params=["ipman_first", "agent_first"])
    def init_order(self, request: pytest.FixtureRequest) -> str:
        return request.param

    def _setup_env(
        self,
        init_order: str,
        agent: str,
        scope: str,
        workspace: Path,
    ) -> tuple[str, Path]:
        """Set up an env honouring the init order. Returns (env_name, config_dir)."""
        config_dir_name = AgentManager.AGENT_CONFIG_DIR[agent]
        config_dir = workspace / config_dir_name
        name = _unique_name()

        if init_order == "ipman_first":
            # Create ipman env first, then ensure agent config dir exists
            run_ipman(
                "env", "create", name, "--agent", agent, f"--{scope}",
                cwd=workspace,
            )
            config_dir.mkdir(exist_ok=True)
        else:
            # Agent config dir first, then ipman env with --inherit
            config_dir.mkdir(exist_ok=True)
            run_ipman(
                "env", "create", name, "--agent", agent, f"--{scope}",
                "--inherit", cwd=workspace,
            )

        return name, config_dir

    def test_env_functional_regardless_of_init_order(
        self, init_order: str, agent: str, scope: str, project_dir: Path,
    ) -> None:
        """Both init orders should produce a working env."""
        name, _config_dir = self._setup_env(
            init_order, agent, scope, project_dir,
        )
        try:
            run_ipman(
                "env", "activate", name, f"--{scope}", cwd=project_dir,
            )
            status = run_ipman("env", "status", cwd=project_dir)
            assert name in status.stdout
        finally:
            run_ipman("env", "deactivate", cwd=project_dir, check=False)
            run_ipman(
                "env", "delete", name, f"--{scope}", "-y",
                cwd=project_dir, check=False,
            )

    def test_existing_files_preserved_when_agent_first(
        self, agent: str, scope: str, project_dir: Path,
    ) -> None:
        """When agent dir exists with files, --inherit preserves them."""
        config_dir_name = AgentManager.AGENT_CONFIG_DIR[agent]
        config_dir = project_dir / config_dir_name
        config_dir.mkdir(exist_ok=True)
        (config_dir / "settings.json").write_text('{"key": "value"}')

        name = _unique_name()
        try:
            run_ipman(
                "env", "create", name, "--agent", agent, f"--{scope}",
                "--inherit", cwd=project_dir,
            )
            run_ipman(
                "env", "activate", name, f"--{scope}", cwd=project_dir,
            )

            # File should be accessible through the symlink
            assert (config_dir / "settings.json").read_text() == '{"key": "value"}'
        finally:
            run_ipman("env", "deactivate", cwd=project_dir, check=False)
            run_ipman(
                "env", "delete", name, f"--{scope}", "-y",
                cwd=project_dir, check=False,
            )

    def test_skill_visible_after_late_ipman_init(
        self, agent: str, scope: str, project_dir: Path,
    ) -> None:
        """Pre-created skill dir is accessible after late ipman --inherit init."""
        config_dir_name = AgentManager.AGENT_CONFIG_DIR[agent]
        config_dir = project_dir / config_dir_name
        config_dir.mkdir(exist_ok=True)

        # Simulate a pre-existing skill directory
        skill_dir = config_dir / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "index.js").write_text("// skill code")

        name = _unique_name()
        try:
            run_ipman(
                "env", "create", name, "--agent", agent, f"--{scope}",
                "--inherit", cwd=project_dir,
            )
            run_ipman(
                "env", "activate", name, f"--{scope}", cwd=project_dir,
            )

            # Skill content should be accessible
            assert (config_dir / "skills" / "my-skill" / "index.js").exists()
        finally:
            run_ipman("env", "deactivate", cwd=project_dir, check=False)
            run_ipman(
                "env", "delete", name, f"--{scope}", "-y",
                cwd=project_dir, check=False,
            )

    def test_symlink_replaces_real_dir_correctly(
        self, agent: str, scope: str, project_dir: Path,
    ) -> None:
        """Physical dir becomes a symlink via --inherit; content is migrated."""
        config_dir_name = AgentManager.AGENT_CONFIG_DIR[agent]
        config_dir = project_dir / config_dir_name
        config_dir.mkdir(exist_ok=True)
        (config_dir / "migrated.txt").write_text("migrated content")

        name = _unique_name()
        try:
            run_ipman(
                "env", "create", name, "--agent", agent, f"--{scope}",
                "--inherit", cwd=project_dir,
            )
            run_ipman(
                "env", "activate", name, f"--{scope}", cwd=project_dir,
            )

            assert PlatformAssert.is_symlink(config_dir)
            assert (config_dir / "migrated.txt").read_text() == "migrated content"
        finally:
            run_ipman("env", "deactivate", cwd=project_dir, check=False)
            run_ipman(
                "env", "delete", name, f"--{scope}", "-y",
                cwd=project_dir, check=False,
            )

    def test_ipman_first_then_agent_does_not_break_symlink(
        self, agent: str, scope: str, project_dir: Path,
    ) -> None:
        """Ipman activate, then writing into config dir does not break the symlink."""
        name = _unique_name()
        config_dir = project_dir / AgentManager.AGENT_CONFIG_DIR[agent]
        try:
            run_ipman(
                "env", "create", name, "--agent", agent, f"--{scope}",
                cwd=project_dir,
            )
            run_ipman(
                "env", "activate", name, f"--{scope}", cwd=project_dir,
            )

            # Simulate agent writing into the config dir after activation
            (config_dir / "agent_file.txt").write_text("written by agent")

            assert PlatformAssert.is_symlink(config_dir)
            assert (config_dir / "agent_file.txt").read_text() == "written by agent"
        finally:
            run_ipman("env", "deactivate", cwd=project_dir, check=False)
            run_ipman(
                "env", "delete", name, f"--{scope}", "-y",
                cwd=project_dir, check=False,
            )

    def test_both_orders_produce_equivalent_state(
        self, agent: str, scope: str, tmp_path: Path,
    ) -> None:
        """Side-by-side: ipman_first and agent_first yield equivalent state."""
        results: dict[str, dict[str, bool]] = {}

        for order in ("ipman_first", "agent_first"):
            workspace = tmp_path / order
            workspace.mkdir()
            config_dir_name = AgentManager.AGENT_CONFIG_DIR[agent]
            (workspace / config_dir_name).mkdir()

            name, config_dir = self._setup_env(order, agent, scope, workspace)
            try:
                run_ipman(
                    "env", "activate", name, f"--{scope}", cwd=workspace,
                )
                status = run_ipman("env", "status", cwd=workspace)
                results[order] = {
                    "has_active": name in status.stdout,
                    "is_symlink": PlatformAssert.is_symlink(config_dir),
                }
            finally:
                run_ipman("env", "deactivate", cwd=workspace, check=False)
                run_ipman(
                    "env", "delete", name, f"--{scope}", "-y",
                    cwd=workspace, check=False,
                )

        # Both orders should produce the same structural outcome
        assert results["ipman_first"] == results["agent_first"], (
            f"State divergence: {results}"
        )
