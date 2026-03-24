"""Tests for agent adapter skill CLI wrapping (subprocess delegation)."""

from __future__ import annotations

import json
import subprocess
from unittest.mock import patch

import pytest

from ipman.agents.base import SkillInfo
from ipman.agents.claude_code import ClaudeCodeAdapter
from ipman.agents.openclaw import OpenClawAdapter

# ---------------------------------------------------------------------------
# ClaudeCodeAdapter skill CLI tests
# ---------------------------------------------------------------------------

class TestClaudeCodeSkillInstall:
    """Test claude plugin install wrapping."""

    def setup_method(self) -> None:
        self.adapter = ClaudeCodeAdapter()

    @patch("subprocess.run")
    def test_install_skill_basic(self, mock_run: object) -> None:
        mock_run.return_value = subprocess.CompletedProcess(  # type: ignore[attr-defined]
            args=[], returncode=0, stdout="Installed web-scraper\n", stderr="",
        )
        result = self.adapter.install_skill("web-scraper")
        mock_run.assert_called_once()  # type: ignore[attr-defined]
        args = mock_run.call_args[0][0]  # type: ignore[attr-defined]
        assert args == ["claude", "plugin", "install", "web-scraper"]
        assert result.returncode == 0

    @patch("subprocess.run")
    def test_install_skill_with_scope(self, mock_run: object) -> None:
        mock_run.return_value = subprocess.CompletedProcess(  # type: ignore[attr-defined]
            args=[], returncode=0, stdout="", stderr="",
        )
        self.adapter.install_skill("web-scraper", scope="user")
        args = mock_run.call_args[0][0]  # type: ignore[attr-defined]
        assert args == ["claude", "plugin", "install", "web-scraper", "-s", "user"]

    @patch("subprocess.run")
    def test_install_skill_with_marketplace(self, mock_run: object) -> None:
        mock_run.return_value = subprocess.CompletedProcess(  # type: ignore[attr-defined]
            args=[], returncode=0, stdout="", stderr="",
        )
        self.adapter.install_skill("web-scraper@my-marketplace")
        args = mock_run.call_args[0][0]  # type: ignore[attr-defined]
        assert args == ["claude", "plugin", "install", "web-scraper@my-marketplace"]

    @patch("subprocess.run")
    def test_install_skill_failure(self, mock_run: object) -> None:
        mock_run.return_value = subprocess.CompletedProcess(  # type: ignore[attr-defined]
            args=[], returncode=1, stdout="", stderr="Plugin not found",
        )
        result = self.adapter.install_skill("nonexistent")
        assert result.returncode == 1


class TestClaudeCodeSkillUninstall:
    """Test claude plugin uninstall wrapping."""

    def setup_method(self) -> None:
        self.adapter = ClaudeCodeAdapter()

    @patch("subprocess.run")
    def test_uninstall_skill(self, mock_run: object) -> None:
        mock_run.return_value = subprocess.CompletedProcess(  # type: ignore[attr-defined]
            args=[], returncode=0, stdout="Uninstalled web-scraper\n", stderr="",
        )
        result = self.adapter.uninstall_skill("web-scraper")
        args = mock_run.call_args[0][0]  # type: ignore[attr-defined]
        assert args == ["claude", "plugin", "uninstall", "web-scraper"]
        assert result.returncode == 0


class TestClaudeCodeSkillList:
    """Test claude plugin list --json wrapping."""

    def setup_method(self) -> None:
        self.adapter = ClaudeCodeAdapter()

    @patch("subprocess.run")
    def test_list_skills_empty(self, mock_run: object) -> None:
        mock_run.return_value = subprocess.CompletedProcess(  # type: ignore[attr-defined]
            args=[], returncode=0, stdout="[]", stderr="",
        )
        skills = self.adapter.list_skills()
        args = mock_run.call_args[0][0]  # type: ignore[attr-defined]
        assert args == ["claude", "plugin", "list", "--json"]
        assert skills == []

    @patch("subprocess.run")
    def test_list_skills_with_results(self, mock_run: object) -> None:
        plugins = [
            {"name": "web-scraper", "version": "1.0.0", "enabled": True},
            {"name": "git-helper", "version": "2.1.0", "enabled": False},
        ]
        mock_run.return_value = subprocess.CompletedProcess(  # type: ignore[attr-defined]
            args=[], returncode=0, stdout=json.dumps(plugins), stderr="",
        )
        skills = self.adapter.list_skills()
        assert len(skills) == 2
        assert skills[0].name == "web-scraper"
        assert skills[0].version == "1.0.0"
        assert skills[1].name == "git-helper"

    @patch("subprocess.run")
    def test_list_skills_command_failure(self, mock_run: object) -> None:
        mock_run.return_value = subprocess.CompletedProcess(  # type: ignore[attr-defined]
            args=[], returncode=1, stdout="", stderr="Error",
        )
        skills = self.adapter.list_skills()
        assert skills == []


# ---------------------------------------------------------------------------
# OpenClawAdapter skill CLI tests
# ---------------------------------------------------------------------------

class TestOpenClawSkillInstall:
    """Test clawhub install wrapping."""

    def setup_method(self) -> None:
        self.adapter = OpenClawAdapter()

    @patch("subprocess.run")
    def test_install_skill_basic(self, mock_run: object) -> None:
        mock_run.return_value = subprocess.CompletedProcess(  # type: ignore[attr-defined]
            args=[], returncode=0, stdout="Installed web-scraper\n", stderr="",
        )
        result = self.adapter.install_skill("web-scraper")
        args = mock_run.call_args[0][0]  # type: ignore[attr-defined]
        assert args == ["clawhub", "install", "web-scraper"]
        assert result.returncode == 0

    @patch("subprocess.run")
    def test_install_skill_with_hub(self, mock_run: object) -> None:
        mock_run.return_value = subprocess.CompletedProcess(  # type: ignore[attr-defined]
            args=[], returncode=0, stdout="", stderr="",
        )
        self.adapter.install_skill("web-scraper", hub="https://custom-hub.com")
        args = mock_run.call_args[0][0]  # type: ignore[attr-defined]
        assert "--hub" in args or "https://custom-hub.com" in args


class TestOpenClawSkillUninstall:
    """Test clawhub uninstall wrapping."""

    def setup_method(self) -> None:
        self.adapter = OpenClawAdapter()

    @patch("subprocess.run")
    def test_uninstall_skill_default_includes_yes(self, mock_run: object) -> None:
        """Default behavior should include --yes for non-interactive safety."""
        mock_run.return_value = subprocess.CompletedProcess(  # type: ignore[attr-defined]
            args=[], returncode=0, stdout="", stderr="",
        )
        result = self.adapter.uninstall_skill("web-scraper")
        args = mock_run.call_args[0][0]  # type: ignore[attr-defined]
        assert args == ["clawhub", "uninstall", "web-scraper", "--yes"]
        assert result.returncode == 0

    @patch("subprocess.run")
    def test_uninstall_skill_explicit_yes(self, mock_run: object) -> None:
        mock_run.return_value = subprocess.CompletedProcess(  # type: ignore[attr-defined]
            args=[], returncode=0, stdout="", stderr="",
        )
        self.adapter.uninstall_skill("web-scraper", auto_yes=True)
        args = mock_run.call_args[0][0]  # type: ignore[attr-defined]
        assert "--yes" in args

    @patch("subprocess.run")
    def test_uninstall_skill_no_yes(self, mock_run: object) -> None:
        mock_run.return_value = subprocess.CompletedProcess(  # type: ignore[attr-defined]
            args=[], returncode=0, stdout="", stderr="",
        )
        self.adapter.uninstall_skill("web-scraper", auto_yes=False)
        args = mock_run.call_args[0][0]  # type: ignore[attr-defined]
        assert "--yes" not in args


class TestOpenClawSkillList:
    """Test openclaw skill list wrapping."""

    def setup_method(self) -> None:
        self.adapter = OpenClawAdapter()

    @patch("subprocess.run")
    def test_list_skills(self, mock_run: object) -> None:
        output = json.dumps([
            {"name": "web-scraper", "version": "1.0.0"},
        ])
        mock_run.return_value = subprocess.CompletedProcess(  # type: ignore[attr-defined]
            args=[], returncode=0, stdout=output, stderr="",
        )
        skills = self.adapter.list_skills()
        assert len(skills) == 1
        assert skills[0].name == "web-scraper"


class TestOpenClawSkillListFallback:
    """Test list_skills 3-strategy fallback: --json -> plain text -> lockfile."""

    def setup_method(self) -> None:
        self.adapter = OpenClawAdapter()

    @patch("subprocess.run")
    def test_list_skills_json_success(self, mock_run) -> None:
        """Strategy 1: --json works — use it."""
        output = json.dumps([
            {"name": "web-scraper", "version": "1.0.0"},
            {"name": "git-helper", "version": "2.0.0"},
        ])
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=output, stderr="",
        )
        skills = self.adapter.list_skills()
        assert len(skills) == 2
        assert skills[0].name == "web-scraper"
        assert skills[1].name == "git-helper"

    @patch("subprocess.run")
    def test_list_skills_json_fails_plain_text_works(self, mock_run) -> None:
        """Strategy 2: --json fails, parse plain text."""
        def side_effect(args, **kwargs):
            if "--json" in args:
                return subprocess.CompletedProcess(
                    args=args, returncode=1,
                    stdout="", stderr="unknown flag: --json",
                )
            return subprocess.CompletedProcess(
                args=args, returncode=0,
                stdout="web-scraper  1.0.0  enabled\ngit-helper  2.0.0  enabled\n",
                stderr="",
            )
        mock_run.side_effect = side_effect
        skills = self.adapter.list_skills()
        assert len(skills) == 2
        assert skills[0].name == "web-scraper"
        assert skills[0].version == "1.0.0"

    @patch("subprocess.run")
    def test_list_skills_both_cli_fail_lockfile_works(self, mock_run, tmp_path) -> None:
        """Strategy 3: both CLI calls fail, read .clawhub/lock.json."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="command not found",
        )
        lock_dir = tmp_path / ".clawhub"
        lock_dir.mkdir()
        lock_file = lock_dir / "lock.json"
        lock_file.write_text(json.dumps({
            "skills": {
                "web-scraper": {"version": "1.0.0"},
                "git-helper": {"version": "2.0.0"},
            }
        }))
        skills = self.adapter.list_skills(workdir=tmp_path)
        assert len(skills) == 2

    @patch("subprocess.run")
    def test_list_skills_all_strategies_fail(self, mock_run) -> None:
        """All strategies fail — return empty list."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="error",
        )
        skills = self.adapter.list_skills()
        assert skills == []

    @patch("subprocess.run")
    def test_list_skills_plain_text_various_formats(self, mock_run) -> None:
        """Parse plain text with different separators."""
        def side_effect(args, **kwargs):
            if "--json" in args:
                return subprocess.CompletedProcess(
                    args=args, returncode=1, stdout="", stderr="",
                )
            return subprocess.CompletedProcess(
                args=args, returncode=0,
                stdout="  skill-a    1.2.3\n  skill-b\n",
                stderr="",
            )
        mock_run.side_effect = side_effect
        skills = self.adapter.list_skills()
        assert len(skills) == 2
        assert skills[0].name == "skill-a"
        assert skills[0].version == "1.2.3"
        assert skills[1].name == "skill-b"
        assert skills[1].version == ""


# ---------------------------------------------------------------------------
# _run_cli error handling tests
# ---------------------------------------------------------------------------

class TestRunCliErrorHandling:
    """Test that _run_cli catches FileNotFoundError."""

    def test_missing_cli_returns_friendly_error(self) -> None:
        """When agent CLI is not installed, return error instead of traceback."""
        adapter = ClaudeCodeAdapter()
        result = adapter._run_cli(["nonexistent-binary-xyz-12345", "list"])
        assert result.returncode == -1
        assert "command not found" in result.stderr
        assert "Claude Code" in result.stderr

    def test_missing_openclaw_cli_returns_friendly_error(self) -> None:
        """OpenClaw adapter should also return friendly error."""
        adapter = OpenClawAdapter()
        result = adapter._run_cli(["nonexistent-binary-xyz-12345", "list"])
        assert result.returncode == -1
        assert "command not found" in result.stderr
        assert "OpenClaw" in result.stderr


# ---------------------------------------------------------------------------
# SkillInfo dataclass tests
# ---------------------------------------------------------------------------

class TestSkillInfo:
    """Test SkillInfo data structure."""

    def test_skill_info_creation(self) -> None:
        info = SkillInfo(name="test-skill", version="1.0.0")
        assert info.name == "test-skill"
        assert info.version == "1.0.0"
        assert info.enabled is True  # default

    def test_skill_info_disabled(self) -> None:
        info = SkillInfo(name="test", version="1.0", enabled=False)
        assert info.enabled is False


# ---------------------------------------------------------------------------
# Adapter interface compliance
# ---------------------------------------------------------------------------

class TestAdapterInterface:
    """Verify both adapters implement the full interface."""

    @pytest.mark.parametrize("adapter_cls", [ClaudeCodeAdapter, OpenClawAdapter])  # type: ignore[type-abstract]
    def test_has_skill_methods(self, adapter_cls: type) -> None:
        adapter = adapter_cls()
        assert hasattr(adapter, "install_skill")
        assert hasattr(adapter, "uninstall_skill")
        assert hasattr(adapter, "list_skills")
        assert callable(adapter.install_skill)
        assert callable(adapter.uninstall_skill)
        assert callable(adapter.list_skills)


# ---------------------------------------------------------------------------
# ClaudeCodeAdapter local skill install tests
# ---------------------------------------------------------------------------

class TestClaudeCodeLocalInstall:
    def setup_method(self) -> None:
        self.adapter = ClaudeCodeAdapter()

    def test_install_local_dir(self, tmp_path):
        """Local directory -> copied to config_dir/skills/."""
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("test skill")
        project = tmp_path / "project"
        project.mkdir()
        (project / ".claude" / "skills").mkdir(parents=True)
        result = self.adapter.install_skill(
            str(skill_dir), config_dir=str(project / ".claude"),
        )
        assert result.returncode == 0
        assert (project / ".claude" / "skills" / "my-skill" / "SKILL.md").exists()

    @patch("subprocess.run")
    def test_install_remote_name(self, mock_run):
        """Non-existent path -> claude plugin install."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr="",
        )
        self.adapter.install_skill("web-scraper")
        args = mock_run.call_args[0][0]
        assert args == ["claude", "plugin", "install", "web-scraper"]


# ---------------------------------------------------------------------------
# OpenClawAdapter local skill install tests
# ---------------------------------------------------------------------------

class TestOpenClawLocalInstall:
    def setup_method(self) -> None:
        self.adapter = OpenClawAdapter()

    def test_install_local_dir(self, tmp_path):
        """Local directory -> copied to config_dir/skills/."""
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("test skill")
        project = tmp_path / "project"
        project.mkdir()
        (project / ".openclaw" / "skills").mkdir(parents=True)
        result = self.adapter.install_skill(
            str(skill_dir), config_dir=str(project / ".openclaw"),
        )
        assert result.returncode == 0
        assert (project / ".openclaw" / "skills" / "my-skill" / "SKILL.md").exists()

    @patch("subprocess.run")
    def test_install_remote_name(self, mock_run):
        """Non-existent path -> clawhub install."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr="",
        )
        self.adapter.install_skill("web-scraper")
        args = mock_run.call_args[0][0]
        assert args == ["clawhub", "install", "web-scraper"]
