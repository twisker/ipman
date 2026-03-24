"""Integration tests for CLI env commands."""

from __future__ import annotations

from click.testing import CliRunner

from ipman.cli.main import cli


class TestEnvCLI:
    def test_env_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["env", "--help"])
        assert result.exit_code == 0
        assert "create" in result.output
        assert "activate" in result.output

    def test_create_and_list(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["env", "create", "myenv"])
            assert result.exit_code == 0
            assert "Created environment 'myenv'" in result.output

            result = runner.invoke(cli, ["env", "list"])
            assert result.exit_code == 0
            assert "myenv" in result.output

    def test_create_duplicate_fails(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(cli, ["env", "create", "myenv"])
            result = runner.invoke(cli, ["env", "create", "myenv"])
            assert result.exit_code == 1

    def test_activate_and_deactivate(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(cli, ["env", "create", "myenv"])
            result = runner.invoke(cli, ["env", "activate", "myenv"])
            assert result.exit_code == 0

            result = runner.invoke(cli, ["env", "deactivate"])
            assert result.exit_code == 0

    def test_delete_with_confirm(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(cli, ["env", "create", "myenv"])
            result = runner.invoke(cli, ["env", "delete", "myenv", "-y"])
            assert result.exit_code == 0
            assert "Deleted" in result.output

    def test_list_empty(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["env", "list"])
            assert result.exit_code == 0
            assert "No environments found" in result.output

    def test_list_shows_active_marker(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(cli, ["env", "create", "env1"])
            runner.invoke(cli, ["env", "create", "env2"])
            runner.invoke(cli, ["env", "activate", "env1"])
            result = runner.invoke(cli, ["env", "list"])
            assert result.exit_code == 0
            assert "env1" in result.output

    def test_status_no_active(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["env", "status"])
            assert result.exit_code == 0
            assert "No active environment" in result.output

    def test_status_with_active(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(cli, ["env", "create", "myenv"])
            runner.invoke(cli, ["env", "activate", "myenv"])
            result = runner.invoke(cli, ["env", "status"])
            assert result.exit_code == 0
            assert "myenv" in result.output
            assert "project" in result.output.lower()
            assert "[ip:myenv]" in result.output

    def test_activate_shows_prompt_tag(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(cli, ["env", "create", "myenv"])
            result = runner.invoke(cli, ["env", "activate", "myenv"])
            assert result.exit_code == 0
            assert "[ip:myenv]" in result.output
