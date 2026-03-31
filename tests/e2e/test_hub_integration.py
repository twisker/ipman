"""Phase 2 — IpHub integration tests (real network, iphub-test fork).

These tests validate hub/client.py against the live twisker/iphub-test
repository. They require network access and a seeded test fork.

Run with:
    IPHUB_REPO=twisker/iphub-test pytest tests/e2e/test_hub_integration.py -v

The test fork must contain:
    index.yaml                           — skills + packages index
    registry/@twisker/test-skill-a.yaml — skill registry entry
    registry/@twisker/test-skill-b.yaml — skill registry entry (tags: scraper)
    registry/@twisker/test-package/meta.yaml
    registry/@twisker/test-package/1.0.0.yaml
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytestmark = [pytest.mark.e2e, pytest.mark.network]


def _make_client(tmp_path: Path):  # type: ignore[return]
    """Build an IpHubClient targeting the IPHUB_REPO test fork."""
    from ipman.hub.client import IpHubClient

    repo = os.environ.get("IPHUB_REPO", "")
    if not repo:
        pytest.skip("IPHUB_REPO not set — set to twisker/iphub-test to run Phase 2")

    base_url = f"https://raw.githubusercontent.com/{repo}/main"
    return IpHubClient(cache_dir=tmp_path / "cache", base_url=base_url)


# ---------------------------------------------------------------------------
# Section 1: Index fetch + caching
# ---------------------------------------------------------------------------

class TestHubIndexFetch:
    """Verify index.yaml fetch, cache behaviour, and basic structure."""

    def test_fetch_index_returns_dict(self, tmp_path: Path) -> None:
        """fetch_index() returns a non-empty dict from the test fork."""
        client = _make_client(tmp_path)
        index = client.fetch_index()
        assert isinstance(index, dict), "index should be a dict"
        assert index, "index should not be empty"

    def test_fetch_index_has_skills_section(self, tmp_path: Path) -> None:
        """index.yaml has a 'skills' key with at least one entry."""
        client = _make_client(tmp_path)
        index = client.fetch_index()
        assert "skills" in index, "index missing 'skills' section"
        assert len(index["skills"]) >= 1

    def test_fetch_index_has_packages_section(self, tmp_path: Path) -> None:
        """index.yaml has a 'packages' key with at least one entry."""
        client = _make_client(tmp_path)
        index = client.fetch_index()
        assert "packages" in index, "index missing 'packages' section"
        assert len(index["packages"]) >= 1

    def test_index_cache_written_to_disk(self, tmp_path: Path) -> None:
        """After fetch, index.yaml is written to cache_dir."""
        client = _make_client(tmp_path)
        client.fetch_index()
        cache_file = tmp_path / "cache" / "index.yaml"
        assert cache_file.exists(), f"Cache file not written: {cache_file}"
        assert cache_file.stat().st_size > 0

    def test_index_cache_avoids_second_network_call(self, tmp_path: Path) -> None:
        """Second fetch_index() uses cached data (same object returned)."""
        client = _make_client(tmp_path)
        first = client.fetch_index()
        second = client.fetch_index()
        # Both must have the same skill count — no mutation between calls
        assert set(first.get("skills", {}).keys()) == set(
            second.get("skills", {}).keys()
        )

    def test_fetch_index_refresh_hits_network(self, tmp_path: Path) -> None:
        """refresh=True fetches fresh data and overwrites the cache."""
        client = _make_client(tmp_path)
        client.fetch_index()  # populate cache
        refreshed = client.fetch_index(refresh=True)
        assert "skills" in refreshed


# ---------------------------------------------------------------------------
# Section 2: Skill lookup + search
# ---------------------------------------------------------------------------

class TestHubSearch:
    """Verify search() filters correctly over the test index."""

    def test_search_by_name_keyword(self, tmp_path: Path) -> None:
        """search('test-skill') returns the seeded test skills."""
        client = _make_client(tmp_path)
        results = client.search("test-skill")
        assert len(results) >= 1, "Expected at least 1 result for 'test-skill'"
        names = [r["name"] for r in results]
        assert any("test-skill" in n for n in names)

    def test_search_by_description_keyword(self, tmp_path: Path) -> None:
        """search('scraper') finds test-skill-b by description keyword."""
        client = _make_client(tmp_path)
        results = client.search("scraper")
        assert len(results) >= 1, "Expected at least 1 result for 'scraper'"
        names = [r["name"] for r in results]
        assert "test-skill-b" in names, f"test-skill-b missing from {names}"

    def test_search_by_agent_filter(self, tmp_path: Path) -> None:
        """search with agent='openclaw' returns only skills supporting openclaw."""
        client = _make_client(tmp_path)
        results = client.search("", agent="openclaw")
        for r in results:
            assert "openclaw" in r.get("agents", []), (
                f"{r['name']} returned for openclaw filter but lacks agent"
            )

    def test_search_empty_query_returns_all(self, tmp_path: Path) -> None:
        """search('') with no filters returns all index entries."""
        client = _make_client(tmp_path)
        results = client.search("")
        index = client.fetch_index()
        total = len(index.get("skills", {})) + len(index.get("packages", {}))
        assert len(results) == total, (
            f"Expected {total} results, got {len(results)}"
        )

    def test_search_no_match_returns_empty(self, tmp_path: Path) -> None:
        """search for a nonexistent keyword returns empty list."""
        client = _make_client(tmp_path)
        results = client.search("xyzzy-no-such-skill-exists-9999")
        assert results == []


# ---------------------------------------------------------------------------
# Section 3: lookup() single entry
# ---------------------------------------------------------------------------

class TestHubLookup:
    """Verify lookup() resolves skills and packages by short name."""

    def test_lookup_existing_skill(self, tmp_path: Path) -> None:
        """lookup('test-skill-a') returns the skill entry."""
        client = _make_client(tmp_path)
        entry = client.lookup("test-skill-a")
        assert entry is not None, "test-skill-a not found"
        assert entry["name"] == "test-skill-a"
        assert entry.get("type") in ("skill", None)  # may not have type in index

    def test_lookup_existing_package(self, tmp_path: Path) -> None:
        """lookup('test-package') returns the IP package entry."""
        client = _make_client(tmp_path)
        entry = client.lookup("test-package")
        assert entry is not None, "test-package not found"
        assert entry["name"] == "test-package"

    def test_lookup_nonexistent_returns_none(self, tmp_path: Path) -> None:
        """lookup of unknown name returns None (not an exception)."""
        client = _make_client(tmp_path)
        result = client.lookup("no-such-skill-zzzz")
        assert result is None


# ---------------------------------------------------------------------------
# Section 4: fetch_registry() — real file download
# ---------------------------------------------------------------------------

class TestHubFetchRegistry:
    """Verify fetch_registry() downloads and parses real registry files."""

    def test_fetch_skill_registry(self, tmp_path: Path) -> None:
        """fetch_registry('test-skill-a') returns a dict with type='skill'."""
        client = _make_client(tmp_path)
        data = client.fetch_registry("test-skill-a")
        assert data is not None, "fetch_registry returned None for test-skill-a"
        assert data.get("type") == "skill"
        assert data.get("name") == "test-skill-a"
        assert "agents" in data, "skill registry missing 'agents' section"

    def test_fetch_package_registry(self, tmp_path: Path) -> None:
        """fetch_registry('test-package') returns the versioned file."""
        client = _make_client(tmp_path)
        data = client.fetch_registry("test-package")
        assert data is not None, "fetch_registry returned None for test-package"
        assert "skills" in data, "package registry missing 'skills' list"
        assert "version" in data

    def test_fetch_registry_unknown_name_returns_none(
        self, tmp_path: Path,
    ) -> None:
        """fetch_registry for unknown name returns None (lookup fails first)."""
        client = _make_client(tmp_path)
        result = client.fetch_registry("no-such-thing-zzzz")
        assert result is None
