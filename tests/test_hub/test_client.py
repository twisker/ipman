"""Tests for IpHub client (index.yaml fetch, cache, search)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ipman.hub.client import IpHubClient

SAMPLE_INDEX = {
    "skills": {
        "web-scraper": {
            "owner": "@twisker",
            "type": "skill",
            "latest": "1.2.0",
            "description": "Browser automation for web scraping",
            "agents": ["claude-code", "openclaw"],
            "installs": 1234,
        },
        "git-helper": {
            "owner": "@alice",
            "type": "skill",
            "latest": "2.0.1",
            "description": "Git workflow automation",
            "agents": ["claude-code"],
            "installs": 890,
        },
    },
    "packages": {
        "frontend-toolkit": {
            "owner": "@twisker",
            "type": "ip",
            "latest": "1.0.0",
            "description": "Essential skills for frontend development",
            "installs": 456,
        },
    },
}

SAMPLE_INDEX_YAML = """\
skills:
  web-scraper:
    owner: "@twisker"
    type: skill
    latest: "1.2.0"
    description: "Browser automation for web scraping"
    agents: [claude-code, openclaw]
    installs: 1234
  git-helper:
    owner: "@alice"
    type: skill
    latest: "2.0.1"
    description: "Git workflow automation"
    agents: [claude-code]
    installs: 890
packages:
  frontend-toolkit:
    owner: "@twisker"
    type: ip
    latest: "1.0.0"
    description: "Essential skills for frontend development"
    installs: 456
"""


class TestIpHubClientFetch:
    """Test index.yaml fetching."""

    @patch("ipman.hub.client.urllib.request.urlopen")
    def test_fetch_index(self, mock_urlopen: MagicMock, tmp_path: Path) -> None:
        mock_response = MagicMock()
        mock_response.read.return_value = SAMPLE_INDEX_YAML.encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        client = IpHubClient(cache_dir=tmp_path)
        index = client.fetch_index()

        assert "skills" in index
        assert "web-scraper" in index["skills"]
        assert index["skills"]["web-scraper"]["owner"] == "@twisker"

    @patch("ipman.hub.client.urllib.request.urlopen")
    def test_fetch_index_caches_locally(self, mock_urlopen: MagicMock, tmp_path: Path) -> None:
        mock_response = MagicMock()
        mock_response.read.return_value = SAMPLE_INDEX_YAML.encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        client = IpHubClient(cache_dir=tmp_path)
        client.fetch_index()
        # Second call should use cache
        client.fetch_index()
        assert mock_urlopen.call_count == 1

    @patch("ipman.hub.client.urllib.request.urlopen")
    def test_fetch_index_refresh_bypasses_cache(self, mock_urlopen: MagicMock, tmp_path: Path) -> None:
        mock_response = MagicMock()
        mock_response.read.return_value = SAMPLE_INDEX_YAML.encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        client = IpHubClient(cache_dir=tmp_path)
        client.fetch_index()
        client.fetch_index(refresh=True)
        assert mock_urlopen.call_count == 2


class TestIpHubClientSearch:
    """Test local index search."""

    def _make_client(self, tmp_path: Path) -> IpHubClient:
        client = IpHubClient(cache_dir=tmp_path)
        client._index = SAMPLE_INDEX  # inject directly for testing
        return client

    def test_search_by_keyword(self, tmp_path: Path) -> None:
        client = self._make_client(tmp_path)
        results = client.search("scraper")
        assert len(results) == 1
        assert results[0]["name"] == "web-scraper"

    def test_search_by_keyword_case_insensitive(self, tmp_path: Path) -> None:
        client = self._make_client(tmp_path)
        results = client.search("GIT")
        assert len(results) == 1
        assert results[0]["name"] == "git-helper"

    def test_search_returns_both_skills_and_packages(self, tmp_path: Path) -> None:
        client = self._make_client(tmp_path)
        results = client.search("frontend")
        assert len(results) == 1
        assert results[0]["type"] == "ip"

    def test_search_no_results(self, tmp_path: Path) -> None:
        client = self._make_client(tmp_path)
        results = client.search("nonexistent-xyz")
        assert results == []

    def test_search_by_agent(self, tmp_path: Path) -> None:
        client = self._make_client(tmp_path)
        results = client.search("", agent="openclaw")
        # Only web-scraper supports openclaw
        names = [r["name"] for r in results]
        assert "web-scraper" in names
        assert "git-helper" not in names

    def test_search_empty_query_returns_all(self, tmp_path: Path) -> None:
        client = self._make_client(tmp_path)
        results = client.search("")
        assert len(results) == 3  # 2 skills + 1 package


class TestIpHubClientLookup:
    """Test single-item lookup."""

    def _make_client(self, tmp_path: Path) -> IpHubClient:
        client = IpHubClient(cache_dir=tmp_path)
        client._index = SAMPLE_INDEX
        return client

    def test_lookup_existing_skill(self, tmp_path: Path) -> None:
        client = self._make_client(tmp_path)
        info = client.lookup("web-scraper")
        assert info is not None
        assert info["name"] == "web-scraper"
        assert info["owner"] == "@twisker"

    def test_lookup_existing_package(self, tmp_path: Path) -> None:
        client = self._make_client(tmp_path)
        info = client.lookup("frontend-toolkit")
        assert info is not None
        assert info["type"] == "ip"

    def test_lookup_nonexistent(self, tmp_path: Path) -> None:
        client = self._make_client(tmp_path)
        info = client.lookup("does-not-exist")
        assert info is None


def test_search_by_tag(tmp_path):
    """search() filters by tag when provided."""
    client = IpHubClient(cache_dir=tmp_path)
    # Inject mock index with tags
    client._index = {
        "skills": {
            "css-helper": {
                "description": "CSS help",
                "tags": ["frontend", "css"],
            },
            "python-lint": {
                "description": "Python linter",
                "tags": ["backend", "python"],
            },
        },
        "packages": {},
    }
    results = client.search("", tag="frontend")
    assert len(results) == 1
    assert results[0]["name"] == "css-helper"


def test_search_by_tag_and_query(tmp_path):
    """search() combines tag filter with keyword query."""
    client = IpHubClient(cache_dir=tmp_path)
    client._index = {
        "skills": {
            "css-helper": {"description": "CSS help", "tags": ["frontend"]},
            "react-patterns": {"description": "React patterns", "tags": ["frontend"]},
        },
        "packages": {},
    }
    results = client.search("react", tag="frontend")
    assert len(results) == 1
    assert results[0]["name"] == "react-patterns"


def test_search_no_tag_returns_all(tmp_path):
    """search() without tag returns all matching entries."""
    client = IpHubClient(cache_dir=tmp_path)
    client._index = {
        "skills": {
            "a": {"description": "x", "tags": ["t1"]},
            "b": {"description": "x", "tags": ["t2"]},
        },
        "packages": {},
    }
    results = client.search("")
    assert len(results) == 2


class TestIpHubClientErrorHandling:
    """Test network and data error handling."""

    @patch("ipman.hub.client.urllib.request.urlopen")
    def test_fetch_index_empty_yaml_raises(
        self, mock_urlopen: MagicMock, tmp_path: Path,
    ) -> None:
        """yaml.safe_load returns None for empty content -> HubError, not AttributeError."""
        from ipman.hub.client import HubError
        mock_response = MagicMock()
        mock_response.read.return_value = b""
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        client = IpHubClient(cache_dir=tmp_path)
        with pytest.raises(HubError, match="empty or malformed"):
            client.fetch_index(refresh=True)

    @patch("ipman.hub.client.urllib.request.urlopen")
    def test_fetch_index_network_error_raises(
        self, mock_urlopen: MagicMock, tmp_path: Path,
    ) -> None:
        """URLError from urlopen -> HubError with descriptive message."""
        import urllib.error
        from ipman.hub.client import HubError
        mock_urlopen.side_effect = urllib.error.URLError("connection refused")

        client = IpHubClient(cache_dir=tmp_path)
        with pytest.raises(HubError, match="Failed to fetch"):
            client.fetch_index(refresh=True)


class TestIpHubClientIndexUrl:
    """Test that base_url properly overrides index_url."""

    def test_base_url_overrides_index_url(self) -> None:
        """When base_url is set, index_url should derive from it."""
        client = IpHubClient(base_url="https://custom.example.com/repo/main")
        assert client._index_url == "https://custom.example.com/repo/main/index.yaml"

    def test_default_index_url(self) -> None:
        """Without override, index_url uses the default GitHub raw URL."""
        client = IpHubClient()
        assert "raw.githubusercontent.com" in client._index_url
        assert client._index_url.endswith("/index.yaml")

    def test_explicit_index_url_preserved(self) -> None:
        """Explicit index_url should be respected even with base_url."""
        client = IpHubClient(
            base_url="https://custom.example.com",
            index_url="https://other.example.com/index.yaml",
        )
        assert client._index_url == "https://other.example.com/index.yaml"

    def test_no_args_uses_default_constant(self) -> None:
        """No args should use the hardcoded _INDEX_URL constant."""
        from ipman.hub.client import _INDEX_URL
        client = IpHubClient()
        assert client._index_url == _INDEX_URL
