"""Tests for `ipman install <file.ip.yaml>` — IP package installation."""

from __future__ import annotations

import subprocess
from pathlib import Path
from textwrap import dedent
from unittest.mock import MagicMock, patch, call

from click.testing import CliRunner

from ipman.cli.main import cli


SAMPLE_IP = dedent("""\
    name: frontend-kit
    version: "2.0.0"
    description: "Frontend development skills"
    skills:
      - name: web-scraper
      - name: css-helper
""")

SAMPLE_IP_WITH_SOURCE = dedent("""\
    name: custom-kit
    version: "1.0.0"
    description: "Kit with direct source"
    skills:
      - name: hub-skill
      - name: private-tool
        source:
          claude-code:
            plugin: "private-tool@our-plugins"
""")


def _mock_adapter(install_ok: bool = True) -> MagicMock:
    adapter = MagicMock()
    adapter.name = "claude-code"
    adapter.display_name = "Claude Code"
    adapter.install_skill.return_value = subprocess.CompletedProcess(
        args=[], returncode=0 if install_ok else 1,
        stdout="OK\n" if install_ok else "",
        stderr="" if install_ok else "Failed",
    )
    return adapter


class TestInstallIPFile:
    """Test `ipman install <file.ip.yaml>`."""

    def test_install_from_ip_file(self, tmp_path: Path) -> None:
        """Install all skills from an IP file."""
        ip_file = tmp_path / "frontend-kit.ip.yaml"
        ip_file.write_text(SAMPLE_IP)
        adapter = _mock_adapter()
        runner = CliRunner()
        with patch("ipman.cli.skill._resolve_agent", return_value=adapter):
            result = runner.invoke(cli, ["install", str(ip_file)])
        assert result.exit_code == 0, result.output
        assert adapter.install_skill.call_count == 2
        adapter.install_skill.assert_any_call("web-scraper")
        adapter.install_skill.assert_any_call("css-helper")

    def test_install_ip_file_reports_count(self, tmp_path: Path) -> None:
        """Output should report how many skills were installed."""
        ip_file = tmp_path / "kit.ip.yaml"
        ip_file.write_text(SAMPLE_IP)
        adapter = _mock_adapter()
        runner = CliRunner()
        with patch("ipman.cli.skill._resolve_agent", return_value=adapter):
            result = runner.invoke(cli, ["install", str(ip_file)])
        assert result.exit_code == 0
        assert "2" in result.output

    def test_install_ip_file_not_found(self) -> None:
        """Non-existent .ip.yaml file should fail gracefully."""
        runner = CliRunner()
        result = runner.invoke(cli, ["install", "/nonexistent/path.ip.yaml"])
        assert result.exit_code != 0

    def test_install_ip_file_partial_failure(self, tmp_path: Path) -> None:
        """If one skill fails, continue and report summary."""
        ip_file = tmp_path / "kit.ip.yaml"
        ip_file.write_text(SAMPLE_IP)
        adapter = _mock_adapter()
        # First skill succeeds, second fails
        adapter.install_skill.side_effect = [
            subprocess.CompletedProcess(args=[], returncode=0, stdout="OK\n", stderr=""),
            subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="Not found"),
        ]
        runner = CliRunner()
        with patch("ipman.cli.skill._resolve_agent", return_value=adapter):
            result = runner.invoke(cli, ["install", str(ip_file)])
        # Should exit with error (partial failure)
        assert result.exit_code != 0
        # Should mention both success and failure
        assert "1" in result.output  # 1 succeeded or 1 failed

    def test_install_ip_file_dry_run(self, tmp_path: Path) -> None:
        """--dry-run should not actually install anything."""
        ip_file = tmp_path / "kit.ip.yaml"
        ip_file.write_text(SAMPLE_IP)
        adapter = _mock_adapter()
        runner = CliRunner()
        with patch("ipman.cli.skill._resolve_agent", return_value=adapter):
            result = runner.invoke(cli, ["install", str(ip_file), "--dry-run"])
        assert result.exit_code == 0
        adapter.install_skill.assert_not_called()
        assert "web-scraper" in result.output
        assert "css-helper" in result.output

    def test_install_ip_file_with_agent_flag(self, tmp_path: Path) -> None:
        """--agent flag should be passed through."""
        ip_file = tmp_path / "kit.ip.yaml"
        ip_file.write_text(SAMPLE_IP)
        adapter = _mock_adapter()
        runner = CliRunner()
        with patch("ipman.cli.skill._resolve_agent", return_value=adapter) as mock_resolve:
            result = runner.invoke(cli, [
                "install", str(ip_file), "--agent", "openclaw",
            ])
        assert result.exit_code == 0
        mock_resolve.assert_called_once_with("openclaw")

    def test_install_single_skill_still_works(self) -> None:
        """Existing `ipman install <name>` behavior is preserved."""
        adapter = MagicMock()
        adapter.display_name = "Claude Code"
        adapter.install_skill.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="OK\n", stderr="",
        )
        runner = CliRunner()
        with patch("ipman.cli.skill._resolve_agent", return_value=adapter):
            result = runner.invoke(cli, ["install", "web-scraper"])
        assert result.exit_code == 0
        adapter.install_skill.assert_called_once_with("web-scraper")

    def test_install_ip_file_empty_skills(self, tmp_path: Path) -> None:
        """IP file with no skills should succeed with 0 installed."""
        ip_file = tmp_path / "empty.ip.yaml"
        ip_file.write_text(dedent("""\
            name: empty-kit
            version: "1.0.0"
            description: "Empty"
            skills: []
        """))
        adapter = _mock_adapter()
        runner = CliRunner()
        with patch("ipman.cli.skill._resolve_agent", return_value=adapter):
            result = runner.invoke(cli, ["install", str(ip_file)])
        assert result.exit_code == 0
        adapter.install_skill.assert_not_called()
