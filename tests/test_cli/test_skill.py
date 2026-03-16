"""Tests for CLI skill commands (install/uninstall/list)."""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from ipman.cli.main import cli
from ipman.cli.skill import _classify_source

# All tests patch _resolve_agent at the point of use in each module
_PATCH_SKILL = "ipman.cli.skill._resolve_agent"
_PATCH_HUB = "ipman.cli.skill._get_hub_client"


class TestSkillInstall:
    """Test `ipman install` command."""

    def setup_method(self) -> None:
        self.runner = CliRunner()

    def test_install_success(self) -> None:
        adapter = MagicMock()
        adapter.name = "claude-code"
        adapter.display_name = "Claude Code"
        adapter.install_skill.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="Installed web-scraper\n", stderr="",
        )
        hub = MagicMock()
        hub.lookup.return_value = {"name": "web-scraper", "type": "skill"}
        hub.fetch_registry.return_value = {"name": "web-scraper", "type": "skill", "agents": {}}

        with patch(_PATCH_SKILL, return_value=adapter), patch(_PATCH_HUB, return_value=hub):
            result = self.runner.invoke(cli, ["install", "web-scraper"])
        assert result.exit_code == 0
        assert "web-scraper" in result.output
        adapter.install_skill.assert_called_once_with("web-scraper")

    def test_install_failure(self) -> None:
        adapter = MagicMock()
        adapter.name = "claude-code"
        adapter.display_name = "Claude Code"
        adapter.install_skill.return_value = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="Plugin not found",
        )
        hub = MagicMock()
        hub.lookup.return_value = {"name": "nonexistent", "type": "skill"}
        hub.fetch_registry.return_value = {"name": "nonexistent", "type": "skill", "agents": {}}

        with patch(_PATCH_SKILL, return_value=adapter), patch(_PATCH_HUB, return_value=hub):
            result = self.runner.invoke(cli, ["install", "nonexistent"])
        assert result.exit_code == 1
        assert "failed" in result.output.lower() or "Plugin not found" in result.output

    def test_install_with_agent_flag(self) -> None:
        adapter = MagicMock()
        adapter.name = "openclaw"
        adapter.display_name = "OpenClaw"
        adapter.install_skill.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="OK\n", stderr="",
        )
        hub = MagicMock()
        hub.lookup.return_value = {"name": "web-scraper", "type": "skill"}
        hub.fetch_registry.return_value = {"name": "web-scraper", "type": "skill", "agents": {}}

        with patch(_PATCH_SKILL, return_value=adapter) as mock_resolve, patch(_PATCH_HUB, return_value=hub):
            result = self.runner.invoke(cli, ["install", "web-scraper", "--agent", "openclaw"])
        assert result.exit_code == 0
        mock_resolve.assert_called_once_with("openclaw")

    def test_install_no_agent_detected(self) -> None:
        import click
        with patch(_PATCH_SKILL, side_effect=click.ClickException("No agent detected. Use --agent to specify one (e.g. --agent claude-code).")):
            result = self.runner.invoke(cli, ["install", "web-scraper"])
        assert result.exit_code == 1
        assert "no agent" in result.output.lower()


class TestSkillUninstall:
    """Test `ipman uninstall` command."""

    def setup_method(self) -> None:
        self.runner = CliRunner()

    def test_uninstall_success(self) -> None:
        adapter = MagicMock()
        adapter.display_name = "Claude Code"
        adapter.uninstall_skill.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="Removed\n", stderr="",
        )
        with patch(_PATCH_SKILL, return_value=adapter):
            result = self.runner.invoke(cli, ["uninstall", "web-scraper"])
        assert result.exit_code == 0
        assert "web-scraper" in result.output
        adapter.uninstall_skill.assert_called_once_with("web-scraper")

    def test_uninstall_failure(self) -> None:
        adapter = MagicMock()
        adapter.display_name = "Claude Code"
        adapter.uninstall_skill.return_value = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="Not installed",
        )
        with patch(_PATCH_SKILL, return_value=adapter):
            result = self.runner.invoke(cli, ["uninstall", "nonexistent"])
        assert result.exit_code == 1


class TestSkillList:
    """Test `ipman skill list` command."""

    def setup_method(self) -> None:
        self.runner = CliRunner()

    def test_list_skills_with_results(self) -> None:
        from ipman.agents.base import SkillInfo

        adapter = MagicMock()
        adapter.display_name = "Claude Code"
        adapter.list_skills.return_value = [
            SkillInfo(name="web-scraper", version="1.0.0"),
            SkillInfo(name="git-helper", version="2.1.0", enabled=False),
        ]
        with patch(_PATCH_SKILL, return_value=adapter):
            result = self.runner.invoke(cli, ["skill", "list"])
        assert result.exit_code == 0
        assert "web-scraper" in result.output
        assert "git-helper" in result.output

    def test_list_skills_empty(self) -> None:
        adapter = MagicMock()
        adapter.display_name = "Claude Code"
        adapter.list_skills.return_value = []
        with patch(_PATCH_SKILL, return_value=adapter):
            result = self.runner.invoke(cli, ["skill", "list"])
        assert result.exit_code == 0

    def test_list_skills_with_agent_flag(self) -> None:
        from ipman.agents.base import SkillInfo

        adapter = MagicMock()
        adapter.display_name = "OpenClaw"
        adapter.list_skills.return_value = [
            SkillInfo(name="test-skill", version="0.1.0"),
        ]
        with patch(_PATCH_SKILL, return_value=adapter) as mock_resolve:
            result = self.runner.invoke(cli, ["skill", "list", "--agent", "openclaw"])
        assert result.exit_code == 0
        assert "test-skill" in result.output
        mock_resolve.assert_called_once_with("openclaw")


class TestClassifySource:
    def test_ip_file(self):
        assert _classify_source("kit.ip.yaml") == "ip_file"

    def test_ip_file_with_path(self):
        assert _classify_source("./path/to/kit.ip.yaml") == "ip_file"

    def test_local_dir(self, tmp_path):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        assert _classify_source(str(skill_dir)) == "local_skill"

    def test_local_dir_relative(self, tmp_path, monkeypatch):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        monkeypatch.chdir(tmp_path)
        assert _classify_source("./my-skill") == "local_skill"

    def test_hub_name(self):
        assert _classify_source("web-scraper") == "hub_name"

    def test_hub_name_not_existing(self):
        assert _classify_source("nonexistent-skill") == "hub_name"
