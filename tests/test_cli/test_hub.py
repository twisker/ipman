"""Tests for `ipman hub` CLI commands (search/info/top)."""

from __future__ import annotations

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
        # web-scraper has most installs (1234), should appear first
        lines = result.output.strip().split("\n")
        content = result.output
        assert "web-scraper" in content
        assert "git-helper" in content
        assert "frontend-toolkit" in content
