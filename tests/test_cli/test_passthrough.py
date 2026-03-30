"""Tests for AgentPassthroughGroup."""
from __future__ import annotations

from unittest.mock import patch, MagicMock
import subprocess

import click
from click.testing import CliRunner

from ipman.cli.passthrough import create_passthrough_group


MOCK_CMD_MAP = {
    "openclaw": ["openclaw", "skills"],
    "claude-code": ["claude", "plugin"],
}


def _build_test_cli(agent_cmd_map: dict | None = None) -> click.Group:
    cmd_map = agent_cmd_map or MOCK_CMD_MAP

    @click.group()
    def cli():
        pass

    group = create_passthrough_group(
        name="skills",
        help="Manage skills.",
        agent_cmd_map=cmd_map,
    )

    @group.command("list")
    def list_cmd():
        click.echo("known-list-output")

    cli.add_command(group, "skills")
    cli.add_command(group, "skill")  # alias
    return cli


class TestKnownSubcommand:
    def test_list_runs_normally(self) -> None:
        cli = _build_test_cli()
        runner = CliRunner()
        result = runner.invoke(cli, ["skills", "list"])
        assert result.exit_code == 0
        assert "known-list-output" in result.output

    def test_alias_skill_equals_skills(self) -> None:
        cli = _build_test_cli()
        runner = CliRunner()
        result = runner.invoke(cli, ["skill", "list"])
        assert result.exit_code == 0
        assert "known-list-output" in result.output


class TestUnknownSubcommandPassthrough:
    @patch("ipman.cli.passthrough.resolve_agent")
    def test_unknown_cmd_passed_to_agent(self, mock_resolve) -> None:
        mock_adapter = MagicMock()
        mock_adapter.name = "openclaw"
        mock_adapter.display_name = "OpenClaw"
        mock_adapter._run_cli.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="agent-output\n", stderr="",
        )
        mock_resolve.return_value = mock_adapter

        cli = _build_test_cli()
        runner = CliRunner()
        result = runner.invoke(cli, ["skills", "enable", "my-skill"])
        assert result.exit_code == 0
        assert "agent-output" in result.output
        mock_adapter._run_cli.assert_called_once_with(
            ["openclaw", "skills", "enable", "my-skill"],
        )

    @patch("ipman.cli.passthrough.resolve_agent")
    def test_unknown_cmd_nonzero_exit(self, mock_resolve) -> None:
        mock_adapter = MagicMock()
        mock_adapter.name = "openclaw"
        mock_adapter.display_name = "OpenClaw"
        mock_adapter._run_cli.return_value = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="error msg\n",
        )
        mock_resolve.return_value = mock_adapter

        cli = _build_test_cli()
        runner = CliRunner()
        result = runner.invoke(cli, ["skills", "enable", "bad-skill"])
        assert result.exit_code == 1

    @patch("ipman.cli.passthrough.resolve_agent")
    def test_passthrough_with_agent_flag(self, mock_resolve) -> None:
        mock_adapter = MagicMock()
        mock_adapter.name = "claude-code"
        mock_adapter.display_name = "Claude Code"
        mock_adapter._run_cli.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="claude-out\n", stderr="",
        )
        mock_resolve.return_value = mock_adapter

        cli = _build_test_cli()
        runner = CliRunner()
        result = runner.invoke(cli, ["skills", "--agent", "claude-code", "enable", "x"])
        assert result.exit_code == 0
        mock_adapter._run_cli.assert_called_once_with(
            ["claude", "plugin", "enable", "x"],
        )


class TestHelpOutput:
    def test_group_help_shows_known_commands(self) -> None:
        cli = _build_test_cli()
        runner = CliRunner()
        result = runner.invoke(cli, ["skills", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output


class TestMainCLIIntegration:
    """Verify skills/plugins commands are registered on the real CLI."""

    def test_skills_command_exists(self) -> None:
        from ipman.cli.main import cli
        runner = CliRunner()
        result = runner.invoke(cli, ["skills", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output

    def test_skill_alias_exists(self) -> None:
        from ipman.cli.main import cli
        runner = CliRunner()
        result = runner.invoke(cli, ["skill", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output

    def test_plugins_command_exists(self) -> None:
        from ipman.cli.main import cli
        runner = CliRunner()
        result = runner.invoke(cli, ["plugins", "--help"])
        assert result.exit_code == 0

    def test_plugin_alias_exists(self) -> None:
        from ipman.cli.main import cli
        runner = CliRunner()
        result = runner.invoke(cli, ["plugin", "--help"])
        assert result.exit_code == 0

    def test_old_install_still_works(self) -> None:
        from ipman.cli.main import cli
        runner = CliRunner()
        result = runner.invoke(cli, ["install", "--help"])
        assert result.exit_code == 0
