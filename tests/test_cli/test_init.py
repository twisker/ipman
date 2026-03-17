"""Tests for ipman init CLI command."""

from unittest.mock import patch

from click.testing import CliRunner

from ipman.cli.main import cli


@patch("ipman.cli.init.config_file_path")
@patch("ipman.cli.init.detect_shell", return_value="bash")
class TestInitCommand:
    def test_init_default(self, mock_detect, mock_path, tmp_path):
        """Auto-detect and inject."""
        cfg = tmp_path / ".bashrc"
        cfg.write_text("", encoding="utf-8")
        mock_path.return_value = cfg
        result = CliRunner().invoke(cli, ["init"])
        assert result.exit_code == 0
        assert "bash" in result.output.lower()
        assert "# >>> ipman init >>>" in cfg.read_text()

    def test_init_specific_shell(self, mock_detect, mock_path, tmp_path):
        cfg = tmp_path / ".bashrc"
        cfg.write_text("", encoding="utf-8")
        mock_path.return_value = cfg
        result = CliRunner().invoke(cli, ["init", "bash"])
        assert result.exit_code == 0
        assert "# >>> ipman init >>>" in cfg.read_text()

    def test_init_reverse(self, mock_detect, mock_path, tmp_path):
        cfg = tmp_path / ".bashrc"
        cfg.write_text("# >>> ipman init >>>\nstuff\n# <<< ipman init <<<\n")
        mock_path.return_value = cfg
        result = CliRunner().invoke(cli, ["init", "--reverse"])
        assert result.exit_code == 0
        assert "# >>> ipman init >>>" not in cfg.read_text()

    def test_init_dry_run(self, mock_detect, mock_path, tmp_path):
        cfg = tmp_path / ".bashrc"
        cfg.write_text("", encoding="utf-8")
        mock_path.return_value = cfg
        result = CliRunner().invoke(cli, ["init", "--dry-run"])
        assert result.exit_code == 0
        assert "ipman()" in result.output
        assert "# >>> ipman init >>>" not in cfg.read_text()

    def test_init_multiple_shells(self, mock_detect, mock_path, tmp_path):
        paths = {"bash": tmp_path / ".bashrc", "zsh": tmp_path / ".zshrc"}
        for p in paths.values():
            p.write_text("", encoding="utf-8")
        mock_path.side_effect = lambda s: paths[s]
        result = CliRunner().invoke(cli, ["init", "bash", "zsh"])
        assert result.exit_code == 0
        for p in paths.values():
            assert "# >>> ipman init >>>" in p.read_text()
