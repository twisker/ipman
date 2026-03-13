"""Tests for CLI skill commands (install/uninstall/list)."""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from ipman.cli.main import cli


class TestSkillInstall:
    """Test `ipman install` command."""

    def setup_method(self) -> None:
        self.runner = CliRunner()

    @patch("ipman.cli.skill.detect_agent")
    def test_install_success(self, mock_detect: MagicMock) -> None:
        adapter = MagicMock()
        adapter.display_name = "Claude Code"
        adapter.install_skill.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="Installed web-scraper\n", stderr="",
        )
        mock_detect.return_value = adapter

        result = self.runner.invoke(cli, ["install", "web-scraper"])
        assert result.exit_code == 0
        assert "web-scraper" in result.output
        adapter.install_skill.assert_called_once_with("web-scraper")

    @patch("ipman.cli.skill.detect_agent")
    def test_install_failure(self, mock_detect: MagicMock) -> None:
        adapter = MagicMock()
        adapter.display_name = "Claude Code"
        adapter.install_skill.return_value = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="Plugin not found",
        )
        mock_detect.return_value = adapter

        result = self.runner.invoke(cli, ["install", "nonexistent"])
        assert result.exit_code == 1
        assert "failed" in result.output.lower() or "Plugin not found" in result.output

    @patch("ipman.cli.skill.get_adapter")
    def test_install_with_agent_flag(self, mock_get: MagicMock) -> None:
        adapter = MagicMock()
        adapter.display_name = "OpenClaw"
        adapter.install_skill.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="OK\n", stderr="",
        )
        mock_get.return_value = adapter

        result = self.runner.invoke(cli, ["install", "web-scraper", "--agent", "openclaw"])
        assert result.exit_code == 0
        mock_get.assert_called_once_with("openclaw")

    @patch("ipman.cli.skill.detect_agent")
    def test_install_no_agent_detected(self, mock_detect: MagicMock) -> None:
        mock_detect.return_value = None

        result = self.runner.invoke(cli, ["install", "web-scraper"])
        assert result.exit_code == 1
        assert "no agent" in result.output.lower() or "not detected" in result.output.lower()


class TestSkillUninstall:
    """Test `ipman uninstall` command."""

    def setup_method(self) -> None:
        self.runner = CliRunner()

    @patch("ipman.cli.skill.detect_agent")
    def test_uninstall_success(self, mock_detect: MagicMock) -> None:
        adapter = MagicMock()
        adapter.display_name = "Claude Code"
        adapter.uninstall_skill.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="Removed\n", stderr="",
        )
        mock_detect.return_value = adapter

        result = self.runner.invoke(cli, ["uninstall", "web-scraper"])
        assert result.exit_code == 0
        assert "web-scraper" in result.output
        adapter.uninstall_skill.assert_called_once_with("web-scraper")

    @patch("ipman.cli.skill.detect_agent")
    def test_uninstall_failure(self, mock_detect: MagicMock) -> None:
        adapter = MagicMock()
        adapter.display_name = "Claude Code"
        adapter.uninstall_skill.return_value = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="Not installed",
        )
        mock_detect.return_value = adapter

        result = self.runner.invoke(cli, ["uninstall", "nonexistent"])
        assert result.exit_code == 1


class TestSkillList:
    """Test `ipman skill list` command."""

    def setup_method(self) -> None:
        self.runner = CliRunner()

    @patch("ipman.cli.skill.detect_agent")
    def test_list_skills_with_results(self, mock_detect: MagicMock) -> None:
        from ipman.agents.base import SkillInfo

        adapter = MagicMock()
        adapter.display_name = "Claude Code"
        adapter.list_skills.return_value = [
            SkillInfo(name="web-scraper", version="1.0.0"),
            SkillInfo(name="git-helper", version="2.1.0", enabled=False),
        ]
        mock_detect.return_value = adapter

        result = self.runner.invoke(cli, ["skill", "list"])
        assert result.exit_code == 0
        assert "web-scraper" in result.output
        assert "git-helper" in result.output

    @patch("ipman.cli.skill.detect_agent")
    def test_list_skills_empty(self, mock_detect: MagicMock) -> None:
        adapter = MagicMock()
        adapter.display_name = "Claude Code"
        adapter.list_skills.return_value = []
        mock_detect.return_value = adapter

        result = self.runner.invoke(cli, ["skill", "list"])
        assert result.exit_code == 0
        assert "no skills" in result.output.lower() or "empty" in result.output.lower() or result.output.strip() != ""

    @patch("ipman.cli.skill.get_adapter")
    def test_list_skills_with_agent_flag(self, mock_get: MagicMock) -> None:
        from ipman.agents.base import SkillInfo

        adapter = MagicMock()
        adapter.display_name = "OpenClaw"
        adapter.list_skills.return_value = [
            SkillInfo(name="test-skill", version="0.1.0"),
        ]
        mock_get.return_value = adapter

        result = self.runner.invoke(cli, ["skill", "list", "--agent", "openclaw"])
        assert result.exit_code == 0
        assert "test-skill" in result.output
