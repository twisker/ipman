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
    generate_injection,
    inject_into_file,
    is_initialized,
    remove_from_file,
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


class TestGenerateInjection:
    def test_bash_has_markers(self) -> None:
        result = generate_injection("bash")
        assert result.startswith(MARKER_START)
        assert result.endswith(MARKER_END)

    def test_bash_has_function(self) -> None:
        result = generate_injection("bash")
        assert "ipman()" in result
        assert "command ipman" in result
        assert "env activate" in result
        assert "env deactivate" in result

    def test_zsh_same_as_bash(self) -> None:
        assert generate_injection("zsh") == generate_injection("bash")

    def test_fish_has_function(self) -> None:
        result = generate_injection("fish")
        assert "function ipman" in result
        assert "command ipman" in result

    def test_powershell_has_function(self) -> None:
        result = generate_injection("powershell")
        assert "function ipman" in result
        assert "Get-Command" in result
        assert "Invoke-Expression" in result
        assert "-join" in result

    def test_unknown_shell_raises(self) -> None:
        with pytest.raises(ValueError, match="tcsh"):
            generate_injection("tcsh")


class TestInjectIntoFile:
    def test_inject_appends_to_file(self, tmp_path: Path) -> None:
        rc = tmp_path / ".bashrc"
        rc.write_text("# existing config\n", encoding="utf-8")
        inject_into_file(rc, "bash")
        content = rc.read_text(encoding="utf-8")
        assert content.startswith("# existing config\n")
        assert MARKER_START in content
        assert MARKER_END in content

    def test_inject_idempotent(self, tmp_path: Path) -> None:
        rc = tmp_path / ".bashrc"
        rc.write_text("# existing\n", encoding="utf-8")
        inject_into_file(rc, "bash")
        inject_into_file(rc, "bash")
        content = rc.read_text(encoding="utf-8")
        assert content.count(MARKER_START) == 1

    def test_inject_upgrade(self, tmp_path: Path) -> None:
        rc = tmp_path / ".bashrc"
        before = "# before\n"
        after = "# after\n"
        old_block = f"{MARKER_START}\n# old content\n{MARKER_END}\n"
        rc.write_text(before + old_block + after, encoding="utf-8")
        inject_into_file(rc, "bash")
        content = rc.read_text(encoding="utf-8")
        assert "# before" in content
        assert "# after" in content
        assert "# old content" not in content
        assert content.count(MARKER_START) == 1

    def test_inject_creates_file_if_missing(self, tmp_path: Path) -> None:
        rc = tmp_path / "subdir" / "deep" / ".bashrc"
        inject_into_file(rc, "bash")
        assert rc.exists()
        content = rc.read_text(encoding="utf-8")
        assert MARKER_START in content

    def test_backup_created(self, tmp_path: Path) -> None:
        rc = tmp_path / ".bashrc"
        original = "# original content\n"
        rc.write_text(original, encoding="utf-8")
        inject_into_file(rc, "bash")
        backup = rc.with_name(rc.name + ".ipman-backup")
        assert backup.exists()
        assert backup.read_text(encoding="utf-8") == original


class TestRemoveFromFile:
    def test_remove_injection(self, tmp_path: Path) -> None:
        rc = tmp_path / ".bashrc"
        content = f"# before\n{MARKER_START}\n# block\n{MARKER_END}\n# after\n"
        rc.write_text(content, encoding="utf-8")
        result = remove_from_file(rc)
        assert result is True
        cleaned = rc.read_text(encoding="utf-8")
        assert MARKER_START not in cleaned
        assert "# before" in cleaned
        assert "# after" in cleaned

    def test_remove_not_present(self, tmp_path: Path) -> None:
        rc = tmp_path / ".bashrc"
        original = "# just config\n"
        rc.write_text(original, encoding="utf-8")
        result = remove_from_file(rc)
        assert result is False
        assert rc.read_text(encoding="utf-8") == original


class TestIsInitialized:
    def test_initialized_true(self, tmp_path: Path) -> None:
        rc = tmp_path / ".bashrc"
        rc.write_text(f"{MARKER_START}\nstuff\n{MARKER_END}\n", encoding="utf-8")
        assert is_initialized(rc) is True

    def test_initialized_false(self, tmp_path: Path) -> None:
        rc = tmp_path / ".bashrc"
        rc.write_text("# no markers\n", encoding="utf-8")
        assert is_initialized(rc) is False

    def test_initialized_file_missing(self, tmp_path: Path) -> None:
        rc = tmp_path / "nonexistent"
        assert is_initialized(rc) is False
