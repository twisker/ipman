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
    def test_uninstall_skill(self, mock_run: object) -> None:
        mock_run.return_value = subprocess.CompletedProcess(  # type: ignore[attr-defined]
            args=[], returncode=0, stdout="", stderr="",
        )
        result = self.adapter.uninstall_skill("web-scraper")
        args = mock_run.call_args[0][0]  # type: ignore[attr-defined]
        assert args == ["clawhub", "uninstall", "web-scraper"]
        assert result.returncode == 0


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

    @pytest.mark.parametrize("adapter_cls", [ClaudeCodeAdapter, OpenClawAdapter])
    def test_has_skill_methods(self, adapter_cls: type) -> None:
        adapter = adapter_cls()
        assert hasattr(adapter, "install_skill")
        assert hasattr(adapter, "uninstall_skill")
        assert hasattr(adapter, "list_skills")
        assert callable(adapter.install_skill)
        assert callable(adapter.uninstall_skill)
        assert callable(adapter.list_skills)
