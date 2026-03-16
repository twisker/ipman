"""Tests for shell detection and config file path resolution."""

from pathlib import Path
from unittest.mock import patch

import pytest

from ipman.core.shell_init import (
    MARKER_END,
    MARKER_START,
    SUPPORTED_SHELLS,
    config_file_path,
    detect_shell,
)


class TestConstants:
    def test_marker_start(self) -> None:
        assert MARKER_START == "# >>> ipman init >>>"

    def test_marker_end(self) -> None:
        assert MARKER_END == "# <<< ipman init <<<"

    def test_supported_shells(self) -> None:
        assert SUPPORTED_SHELLS == ("bash", "zsh", "fish", "powershell")


class TestDetectShell:
    def test_detect_bash(self) -> None:
        with patch.dict("os.environ", {"SHELL": "/bin/bash"}, clear=True):
            assert detect_shell() == "bash"

    def test_detect_zsh(self) -> None:
        with patch.dict("os.environ", {"SHELL": "/bin/zsh"}, clear=True):
            assert detect_shell() == "zsh"

    def test_detect_zsh_not_bash(self) -> None:
        with patch.dict("os.environ", {"SHELL": "/usr/bin/zsh"}, clear=True):
            assert detect_shell() == "zsh"

    def test_detect_fish(self) -> None:
        with patch.dict("os.environ", {"SHELL": "/usr/bin/fish"}, clear=True):
            assert detect_shell() == "fish"

    def test_detect_powershell(self) -> None:
        env = {"PSModulePath": "/some/path"}
        with patch.dict("os.environ", env, clear=True):
            assert detect_shell() == "powershell"

    def test_detect_fallback(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            assert detect_shell() == "bash"


class TestConfigFilePath:
    def test_bash_path(self) -> None:
        assert config_file_path("bash") == Path.home() / ".bashrc"

    def test_zsh_path(self) -> None:
        assert config_file_path("zsh") == Path.home() / ".zshrc"

    def test_fish_path(self) -> None:
        assert config_file_path("fish") == Path.home() / ".config" / "fish" / "config.fish"

    def test_powershell_path(self) -> None:
        result = config_file_path("powershell")
        assert "PowerShell" in str(result)
        assert result.name == "Microsoft.PowerShell_profile.ps1"

    def test_unknown_raises(self) -> None:
        with pytest.raises(ValueError, match="tcsh"):
            config_file_path("tcsh")
