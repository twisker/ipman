"""Tests for install command security integration."""

from __future__ import annotations

import subprocess
from pathlib import Path
from textwrap import dedent
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from ipman.cli.main import cli
from ipman.core.vetter import RiskLevel

SAMPLE_IP = dedent("""\
    name: test-kit
    version: "1.0.0"
    description: "Test"
    skills:
      - name: skill-a
""")


def _mock_adapter() -> MagicMock:
    adapter = MagicMock()
    adapter.name = "claude-code"
    adapter.display_name = "Claude Code"
    adapter.install_skill.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="OK\n", stderr="",
    )
    return adapter


def _mock_hub() -> MagicMock:
    hub = MagicMock()
    hub.lookup.return_value = {"name": "web-scraper", "type": "skill"}
    hub.fetch_registry.return_value = {"name": "web-scraper", "type": "skill", "agents": {}}
    return hub


def _mock_vet_report(risk: RiskLevel) -> MagicMock:
    from ipman.core.vetter import VetReport
    return VetReport(
        skill_name="test",
        risk_level=risk,
        verdict="SAFE" if risk == RiskLevel.LOW else "RISKY",
        flags=[],
    )


class TestInstallSecurityIntegration:
    """Test install command with security mode enforcement."""

    def test_local_ip_file_triggers_vet(self, tmp_path: Path) -> None:
        """Local .ip.yaml install should trigger risk assessment."""
        ip_file = tmp_path / "kit.ip.yaml"
        ip_file.write_text(SAMPLE_IP)
        adapter = _mock_adapter()
        runner = CliRunner()
        with (
            patch("ipman.cli.skill._resolve_agent", return_value=adapter),
            patch("ipman.cli.skill._run_vet", return_value=_mock_vet_report(RiskLevel.LOW)) as mock_vet,
        ):
            result = runner.invoke(cli, ["install", str(ip_file)])
        assert result.exit_code == 0, result.output
        mock_vet.assert_called_once()

    def test_local_ip_file_no_vet_flag_skips(self, tmp_path: Path) -> None:
        """--no-vet should skip local risk assessment."""
        ip_file = tmp_path / "kit.ip.yaml"
        ip_file.write_text(SAMPLE_IP)
        adapter = _mock_adapter()
        runner = CliRunner()
        with (
            patch("ipman.cli.skill._resolve_agent", return_value=adapter),
            patch("ipman.cli.skill._run_vet") as mock_vet,
        ):
            result = runner.invoke(cli, ["install", str(ip_file), "--no-vet"])
        assert result.exit_code == 0
        mock_vet.assert_not_called()

    def test_hub_install_skips_vet_by_default(self) -> None:
        """IpHub install should trust existing label (no local vet)."""
        adapter = _mock_adapter()
        hub = _mock_hub()
        runner = CliRunner()
        with (
            patch("ipman.cli.skill._resolve_agent", return_value=adapter),
            patch("ipman.cli.skill._get_hub_client", return_value=hub),
            patch("ipman.cli.skill._run_vet") as mock_vet,
        ):
            result = runner.invoke(cli, ["install", "web-scraper"])
        assert result.exit_code == 0
        mock_vet.assert_not_called()

    def test_hub_install_with_vet_flag(self) -> None:
        """--vet should force local assessment on IpHub skill."""
        adapter = _mock_adapter()
        hub = _mock_hub()
        runner = CliRunner()
        with (
            patch("ipman.cli.skill._resolve_agent", return_value=adapter),
            patch("ipman.cli.skill._get_hub_client", return_value=hub),
            patch("ipman.cli.skill._run_vet", return_value=_mock_vet_report(RiskLevel.LOW)) as mock_vet,
        ):
            result = runner.invoke(cli, ["install", "web-scraper", "--vet"])
        assert result.exit_code == 0
        mock_vet.assert_called_once()

    def test_block_on_extreme_risk(self, tmp_path: Path) -> None:
        """EXTREME risk should block install in DEFAULT mode."""
        ip_file = tmp_path / "bad.ip.yaml"
        ip_file.write_text(SAMPLE_IP)
        adapter = _mock_adapter()
        runner = CliRunner()
        with (
            patch("ipman.cli.skill._resolve_agent", return_value=adapter),
            patch("ipman.cli.skill._run_vet", return_value=_mock_vet_report(RiskLevel.EXTREME)),
        ):
            result = runner.invoke(cli, ["install", str(ip_file)])
        assert result.exit_code != 0
        adapter.install_skill.assert_not_called()

    def test_warn_on_high_risk_default_mode(self, tmp_path: Path) -> None:
        """HIGH risk in DEFAULT mode should warn but install."""
        ip_file = tmp_path / "risky.ip.yaml"
        ip_file.write_text(SAMPLE_IP)
        adapter = _mock_adapter()
        runner = CliRunner()
        with (
            patch("ipman.cli.skill._resolve_agent", return_value=adapter),
            patch("ipman.cli.skill._run_vet", return_value=_mock_vet_report(RiskLevel.HIGH)),
        ):
            result = runner.invoke(cli, ["install", str(ip_file)])
        assert result.exit_code == 0
        adapter.install_skill.assert_called()

    def test_security_cautious_blocks_high(self, tmp_path: Path) -> None:
        """CAUTIOUS mode should block HIGH risk."""
        ip_file = tmp_path / "risky.ip.yaml"
        ip_file.write_text(SAMPLE_IP)
        adapter = _mock_adapter()
        runner = CliRunner()
        with (
            patch("ipman.cli.skill._resolve_agent", return_value=adapter),
            patch("ipman.cli.skill._run_vet", return_value=_mock_vet_report(RiskLevel.HIGH)),
        ):
            result = runner.invoke(cli, ["install", str(ip_file), "--security", "cautious"])
        assert result.exit_code != 0
        adapter.install_skill.assert_not_called()

    def test_security_permissive_allows_extreme(self, tmp_path: Path) -> None:
        """PERMISSIVE mode should allow even EXTREME (with warning)."""
        ip_file = tmp_path / "evil.ip.yaml"
        ip_file.write_text(SAMPLE_IP)
        adapter = _mock_adapter()
        runner = CliRunner()
        with (
            patch("ipman.cli.skill._resolve_agent", return_value=adapter),
            patch("ipman.cli.skill._run_vet", return_value=_mock_vet_report(RiskLevel.EXTREME)),
        ):
            result = runner.invoke(cli, ["install", str(ip_file), "--security", "permissive"])
        assert result.exit_code == 0
        adapter.install_skill.assert_called()
