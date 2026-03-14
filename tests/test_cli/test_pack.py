"""Tests for `ipman pack` CLI command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import yaml
from click.testing import CliRunner

from ipman.agents.base import SkillInfo
from ipman.cli.main import cli


def _mock_adapter(skills: list[SkillInfo] | None = None) -> MagicMock:
    """Create a mock AgentAdapter with the given skills."""
    adapter = MagicMock()
    adapter.name = "claude-code"
    adapter.display_name = "Claude Code"
    adapter.list_skills.return_value = skills or []
    return adapter


class TestPackCommand:
    """Test `ipman pack` CLI."""

    def test_pack_basic(self, tmp_path: Path) -> None:
        """Pack with default options produces a valid .ip.yaml."""
        adapter = _mock_adapter([
            SkillInfo(name="web-scraper"),
            SkillInfo(name="css-helper", version="1.2.0"),
        ])
        output = tmp_path / "my-pack.ip.yaml"
        runner = CliRunner()
        with patch("ipman.cli.pack._resolve_agent", return_value=adapter):
            result = runner.invoke(cli, [
                "pack",
                "--name", "my-pack",
                "--version", "1.0.0",
                "--output", str(output),
            ])
        assert result.exit_code == 0, result.output
        assert output.exists()
        data = yaml.safe_load(output.read_text())
        assert data["name"] == "my-pack"
        assert data["version"] == "1.0.0"
        assert len(data["skills"]) == 2
        assert data["skills"][0]["name"] == "web-scraper"
        assert data["skills"][1]["name"] == "css-helper"

    def test_pack_no_skills(self, tmp_path: Path) -> None:
        """Pack with no skills should still succeed (empty skills list)."""
        adapter = _mock_adapter([])
        output = tmp_path / "empty.ip.yaml"
        runner = CliRunner()
        with patch("ipman.cli.pack._resolve_agent", return_value=adapter):
            result = runner.invoke(cli, [
                "pack",
                "--name", "empty",
                "--output", str(output),
            ])
        assert result.exit_code == 0
        data = yaml.safe_load(output.read_text())
        assert data["skills"] == []

    def test_pack_default_version(self, tmp_path: Path) -> None:
        """Default version should be 1.0.0."""
        adapter = _mock_adapter([SkillInfo(name="foo")])
        output = tmp_path / "test.ip.yaml"
        runner = CliRunner()
        with patch("ipman.cli.pack._resolve_agent", return_value=adapter):
            result = runner.invoke(cli, [
                "pack",
                "--name", "test",
                "--output", str(output),
            ])
        assert result.exit_code == 0
        data = yaml.safe_load(output.read_text())
        assert data["version"] == "1.0.0"

    def test_pack_custom_description(self, tmp_path: Path) -> None:
        """Pack with custom description."""
        adapter = _mock_adapter([SkillInfo(name="foo")])
        output = tmp_path / "test.ip.yaml"
        runner = CliRunner()
        with patch("ipman.cli.pack._resolve_agent", return_value=adapter):
            result = runner.invoke(cli, [
                "pack",
                "--name", "test",
                "--description", "My custom description",
                "--output", str(output),
            ])
        assert result.exit_code == 0
        data = yaml.safe_load(output.read_text())
        assert data["description"] == "My custom description"

    def test_pack_header_comment(self, tmp_path: Path) -> None:
        """Output file should contain IpMan header comment."""
        adapter = _mock_adapter([SkillInfo(name="foo")])
        output = tmp_path / "test.ip.yaml"
        runner = CliRunner()
        with patch("ipman.cli.pack._resolve_agent", return_value=adapter):
            result = runner.invoke(cli, [
                "pack",
                "--name", "test",
                "--output", str(output),
            ])
        assert result.exit_code == 0
        text = output.read_text()
        assert "https://github.com/twisker/ipman" in text
        assert "ipman install" in text

    def test_pack_output_defaults_to_name(self, tmp_path: Path) -> None:
        """When --output is omitted, file is named <name>.ip.yaml in cwd."""
        adapter = _mock_adapter([SkillInfo(name="foo")])
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            with patch("ipman.cli.pack._resolve_agent", return_value=adapter):
                result = runner.invoke(cli, [
                    "pack",
                    "--name", "my-pack",
                ])
            assert result.exit_code == 0
            output = Path(td) / "my-pack.ip.yaml"
            assert output.exists()

    def test_pack_refuses_overwrite_without_force(self, tmp_path: Path) -> None:
        """Should refuse to overwrite existing file without --force."""
        adapter = _mock_adapter([SkillInfo(name="foo")])
        output = tmp_path / "existing.ip.yaml"
        output.write_text("old content")
        runner = CliRunner()
        with patch("ipman.cli.pack._resolve_agent", return_value=adapter):
            result = runner.invoke(cli, [
                "pack",
                "--name", "existing",
                "--output", str(output),
            ])
        assert result.exit_code != 0
        assert "already exists" in result.output.lower() or "already exists" in (result.exception and str(result.exception) or "").lower()
        # File should not be modified
        assert output.read_text() == "old content"

    def test_pack_force_overwrite(self, tmp_path: Path) -> None:
        """--force should allow overwriting existing file."""
        adapter = _mock_adapter([SkillInfo(name="foo")])
        output = tmp_path / "existing.ip.yaml"
        output.write_text("old content")
        runner = CliRunner()
        with patch("ipman.cli.pack._resolve_agent", return_value=adapter):
            result = runner.invoke(cli, [
                "pack",
                "--name", "existing",
                "--output", str(output),
                "--force",
            ])
        assert result.exit_code == 0
        assert output.read_text() != "old content"

    def test_pack_agent_flag(self, tmp_path: Path) -> None:
        """--agent flag should be passed through to resolver."""
        adapter = _mock_adapter([SkillInfo(name="foo")])
        output = tmp_path / "test.ip.yaml"
        runner = CliRunner()
        with patch("ipman.cli.pack._resolve_agent", return_value=adapter) as mock_resolve:
            result = runner.invoke(cli, [
                "pack",
                "--name", "test",
                "--agent", "openclaw",
                "--output", str(output),
            ])
        assert result.exit_code == 0
        mock_resolve.assert_called_once_with("openclaw")

    def test_pack_roundtrip_parseable(self, tmp_path: Path) -> None:
        """Output of pack should be parseable by parse_ip_file."""
        from ipman.core.package import parse_ip_file

        adapter = _mock_adapter([
            SkillInfo(name="web-scraper", version="2.0"),
            SkillInfo(name="css-helper"),
        ])
        output = tmp_path / "roundtrip.ip.yaml"
        runner = CliRunner()
        with patch("ipman.cli.pack._resolve_agent", return_value=adapter):
            result = runner.invoke(cli, [
                "pack",
                "--name", "roundtrip-test",
                "--version", "3.0.0",
                "--description", "Roundtrip test",
                "--output", str(output),
            ])
        assert result.exit_code == 0
        pkg = parse_ip_file(output)
        assert pkg.name == "roundtrip-test"
        assert pkg.version == "3.0.0"
        assert len(pkg.skills) == 2
