"""Tests for `ipman hub` CLI commands (search/info/top/publish)."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from ipman.cli.main import cli

SAMPLE_INDEX = {
    "skills": {
        "web-scraper": {
            "owner": "@twisker",
            "type": "skill",
            "description": "Browser automation for web scraping",
            "agents": ["claude-code", "openclaw"],
            "installs": 1234,
            "unique_users": 567,
        },
        "git-helper": {
            "owner": "@alice",
            "type": "skill",
            "description": "Git workflow automation",
            "agents": ["claude-code"],
            "installs": 890,
            "unique_users": 234,
        },
    },
    "packages": {
        "frontend-toolkit": {
            "owner": "@twisker",
            "type": "ip",
            "latest": "2.0.0",
            "versions": ["2.0.0", "1.0.0"],
            "description": "Essential skills for frontend development",
            "installs": 456,
            "unique_users": 123,
        },
    },
}


def _mock_hub() -> MagicMock:
    hub = MagicMock()
    hub._index = SAMPLE_INDEX
    hub.fetch_index.return_value = SAMPLE_INDEX
    hub.search.side_effect = lambda q, agent=None: [
        {"name": n, **info}
        for section in ("skills", "packages")
        for n, info in SAMPLE_INDEX.get(section, {}).items()
        if (not q or q.lower() in n.lower() or q.lower() in info.get("description", "").lower())
        and (not agent or agent in info.get("agents", []))
    ]
    hub.lookup.side_effect = lambda name: (
        {"name": name, **SAMPLE_INDEX["skills"][name]}
        if name in SAMPLE_INDEX["skills"]
        else (
            {"name": name, **SAMPLE_INDEX["packages"][name]}
            if name in SAMPLE_INDEX["packages"]
            else None
        )
    )
    return hub


class TestHubSearch:
    """Test `ipman hub search`."""

    def test_search_by_keyword(self) -> None:
        hub = _mock_hub()
        runner = CliRunner()
        with patch("ipman.cli.hub._get_hub_client", return_value=hub):
            result = runner.invoke(cli, ["hub", "search", "scraper"])
        assert result.exit_code == 0, result.output
        assert "web-scraper" in result.output

    def test_search_no_results(self) -> None:
        hub = _mock_hub()
        runner = CliRunner()
        with patch("ipman.cli.hub._get_hub_client", return_value=hub):
            result = runner.invoke(cli, ["hub", "search", "nonexistent-xyz"])
        assert result.exit_code == 0
        assert "no results" in result.output.lower() or result.output.strip() != ""

    def test_search_with_agent_filter(self) -> None:
        hub = _mock_hub()
        runner = CliRunner()
        with patch("ipman.cli.hub._get_hub_client", return_value=hub):
            result = runner.invoke(cli, ["hub", "search", "", "--agent", "openclaw"])
        assert result.exit_code == 0
        assert "web-scraper" in result.output
        assert "git-helper" not in result.output

    def test_search_shows_type(self) -> None:
        hub = _mock_hub()
        runner = CliRunner()
        with patch("ipman.cli.hub._get_hub_client", return_value=hub):
            result = runner.invoke(cli, ["hub", "search", "frontend"])
        assert result.exit_code == 0
        assert "frontend-toolkit" in result.output


class TestHubInfo:
    """Test `ipman hub info`."""

    def test_info_skill(self) -> None:
        hub = _mock_hub()
        runner = CliRunner()
        with patch("ipman.cli.hub._get_hub_client", return_value=hub):
            result = runner.invoke(cli, ["hub", "info", "web-scraper"])
        assert result.exit_code == 0, result.output
        assert "web-scraper" in result.output
        assert "@twisker" in result.output

    def test_info_package(self) -> None:
        hub = _mock_hub()
        runner = CliRunner()
        with patch("ipman.cli.hub._get_hub_client", return_value=hub):
            result = runner.invoke(cli, ["hub", "info", "frontend-toolkit"])
        assert result.exit_code == 0
        assert "frontend-toolkit" in result.output
        assert "2.0.0" in result.output

    def test_info_not_found(self) -> None:
        hub = _mock_hub()
        runner = CliRunner()
        with patch("ipman.cli.hub._get_hub_client", return_value=hub):
            result = runner.invoke(cli, ["hub", "info", "nonexistent"])
        assert result.exit_code != 0


class TestHubTop:
    """Test `ipman hub top`."""

    def test_top_shows_ranked_list(self) -> None:
        hub = _mock_hub()
        runner = CliRunner()
        with patch("ipman.cli.hub._get_hub_client", return_value=hub):
            result = runner.invoke(cli, ["hub", "top"])
        assert result.exit_code == 0, result.output
        content = result.output
        assert "web-scraper" in content
        assert "git-helper" in content
        assert "frontend-toolkit" in content


SAMPLE_IP_FILE = dedent("""\
    name: my-toolkit
    version: "1.0.0"
    description: "My toolkit"
    skills:
      - name: skill-a
""")


class TestHubPublish:
    """Test `ipman hub publish`."""

    @patch("ipman.cli.hub.IpHubPublisher")
    @patch("ipman.cli.hub.get_github_username", return_value="twisker")
    def test_publish_skill(self, mock_user: MagicMock, mock_pub_cls: MagicMock) -> None:
        publisher = MagicMock()
        publisher.publish_skill.return_value = "https://github.com/twisker/iphub/pull/1"
        mock_pub_cls.return_value = publisher

        runner = CliRunner()
        result = runner.invoke(cli, [
            "hub", "publish", "web-scraper",
            "--description", "Browser automation",
        ])
        assert result.exit_code == 0, result.output
        assert "pull/1" in result.output
        publisher.publish_skill.assert_called_once()

    @patch("ipman.cli.hub.IpHubPublisher")
    @patch("ipman.cli.hub.get_github_username", return_value="twisker")
    def test_publish_skill_requires_description(self, mock_user: MagicMock, mock_pub_cls: MagicMock) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["hub", "publish", "web-scraper"])
        assert result.exit_code != 0
        assert "description" in result.output.lower()

    @patch("ipman.cli.hub.IpHubPublisher")
    @patch("ipman.cli.hub.get_github_username", return_value="twisker")
    def test_publish_package(self, mock_user: MagicMock, mock_pub_cls: MagicMock, tmp_path: Path) -> None:
        publisher = MagicMock()
        publisher.publish_package.return_value = "https://github.com/twisker/iphub/pull/2"
        mock_pub_cls.return_value = publisher

        ip_file = tmp_path / "my-toolkit.ip.yaml"
        ip_file.write_text(SAMPLE_IP_FILE)

        runner = CliRunner()
        result = runner.invoke(cli, ["hub", "publish", str(ip_file)])
        assert result.exit_code == 0, result.output
        assert "pull/2" in result.output
        publisher.publish_package.assert_called_once()

    @patch("ipman.cli.hub.get_github_username")
    def test_publish_not_authenticated(self, mock_user: MagicMock) -> None:
        from ipman.hub.publisher import PublishError
        mock_user.side_effect = PublishError("GitHub authentication required.")

        runner = CliRunner()
        result = runner.invoke(cli, [
            "hub", "publish", "test", "--description", "x",
        ])
        assert result.exit_code != 0
        assert "github" in result.output.lower() or "auth" in result.output.lower()

    @patch("ipman.cli.hub.IpHubPublisher")
    @patch("ipman.cli.hub.get_github_username", return_value="twisker")
    @patch("ipman.cli.hub.vet_skill_content", return_value=[])
    def test_publish_clean_skill_passes(self, mock_vet: MagicMock, mock_user: MagicMock, mock_pub_cls: MagicMock) -> None:
        publisher = MagicMock()
        publisher.publish_skill.return_value = "https://github.com/twisker/iphub/pull/5"
        mock_pub_cls.return_value = publisher

        runner = CliRunner()
        result = runner.invoke(cli, ["hub", "publish", "clean-skill", "--description", "Safe tool"])
        assert result.exit_code == 0, result.output
        publisher.publish_skill.assert_called_once()

    @patch("ipman.cli.hub.get_github_username", return_value="twisker")
    @patch("ipman.cli.hub.vet_skill_content")
    def test_publish_blocks_high_risk_skill(self, mock_vet: MagicMock, mock_user: MagicMock) -> None:
        from ipman.core.vetter import RiskFlag, RiskLevel
        mock_vet.return_value = [RiskFlag(id="credential-access", description="Reads ~/.ssh", severity=RiskLevel.HIGH)]

        runner = CliRunner()
        result = runner.invoke(cli, ["hub", "publish", "bad-skill", "--description", "Steals keys"])
        assert result.exit_code != 0
        assert "blocked" in result.output.lower() or "high" in result.output.lower()

    @patch("ipman.cli.hub.IpHubPublisher")
    @patch("ipman.cli.hub.get_github_username", return_value="twisker")
    @patch("ipman.cli.hub.vet_skill_content", return_value=[])
    def test_publish_package_with_vet(self, mock_vet: MagicMock, mock_user: MagicMock, mock_pub_cls: MagicMock, tmp_path: Path) -> None:
        publisher = MagicMock()
        publisher.publish_package.return_value = "https://github.com/twisker/iphub/pull/6"
        mock_pub_cls.return_value = publisher

        ip_file = tmp_path / "kit.ip.yaml"
        ip_file.write_text(SAMPLE_IP_FILE)

        runner = CliRunner()
        result = runner.invoke(cli, ["hub", "publish", str(ip_file)])
        assert result.exit_code == 0, result.output
        mock_vet.assert_called_once()
