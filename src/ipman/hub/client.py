"""IpHub client — fetch, cache, and search the index."""

from __future__ import annotations

import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import yaml


class HubError(Exception):
    """Raised when an IpHub network or data operation fails."""

_DEFAULT_REPO = "twisker/iphub"
_DEFAULT_BRANCH = "main"
_INDEX_URL = (
    "https://raw.githubusercontent.com"
    f"/{_DEFAULT_REPO}/{_DEFAULT_BRANCH}/index.yaml"
)
_CACHE_TTL_SECONDS = 3600  # 1 hour


class IpHubClient:
    """Client for reading the IpHub reference registry.

    Fetches index.yaml from GitHub, caches locally, and provides
    search/lookup over the index.
    """

    def __init__(
        self,
        cache_dir: Path | None = None,
        index_url: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self._base_url = base_url or (
            "https://raw.githubusercontent.com"
            f"/{_DEFAULT_REPO}/{_DEFAULT_BRANCH}"
        )
        # index_url priority: explicit > derived from base_url > default
        if index_url:
            self._index_url = index_url
        elif base_url:
            self._index_url = f"{self._base_url}/index.yaml"
        else:
            self._index_url = _INDEX_URL
        self._cache_dir = cache_dir or Path.home() / ".ipman" / "cache"
        self._cache_file = self._cache_dir / "index.yaml"
        self._index: dict[str, Any] | None = None

    def fetch_index(
        self, refresh: bool = False,
    ) -> dict[str, Any]:
        """Fetch index.yaml, using local cache if fresh."""
        if not refresh and self._index is not None:
            return self._index

        if not refresh and self._cache_file.exists():
            age = time.time() - self._cache_file.stat().st_mtime
            if age < _CACHE_TTL_SECONDS:
                self._index = yaml.safe_load(
                    self._cache_file.read_text(),
                )
                return self._index

        # Fetch from remote
        try:
            with urllib.request.urlopen(self._index_url, timeout=30) as resp:
                raw = resp.read().decode()
        except urllib.error.URLError as exc:
            raise HubError(f"Failed to fetch IpHub index: {exc}") from exc
        except yaml.YAMLError as exc:
            raise HubError(f"Malformed IpHub index YAML: {exc}") from exc

        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache_file.write_text(raw)
        self._index = yaml.safe_load(raw)
        if self._index is None:
            raise HubError("IpHub index is empty or malformed")
        return self._index

    def search(
        self,
        query: str,
        agent: str | None = None,
        tag: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search index by keyword and optional agent filter."""
        index = self._index or self.fetch_index()
        results: list[dict[str, Any]] = []
        q = query.lower()

        for section in ("skills", "packages"):
            items = index.get(section, {})
            for name, info in items.items():
                if agent and agent not in info.get("agents", []):
                    continue
                if tag and tag not in info.get("tags", []):
                    continue
                desc = info.get("description", "").lower()
                if q and q not in name.lower() and q not in desc:
                    continue
                entry = {
                    "name": name,
                    "type": info.get("type", section),
                    **info,
                }
                results.append(entry)

        return results

    def lookup(self, name: str) -> dict[str, Any] | None:
        """Look up a single skill or package by short name."""
        index = self._index or self.fetch_index()
        for section in ("skills", "packages"):
            items = index.get(section, {})
            if name in items:
                return {"name": name, **items[name]}
        return None

    def fetch_registry(
        self, name: str, version: str | None = None,
    ) -> dict[str, Any] | None:
        """Fetch the full registry file for a skill or package.

        For skills: fetches registry/@owner/<name>.yaml
        For packages: fetches registry/@owner/<name>/<version>.yaml
                      (defaults to latest version from index)
        """
        info = self.lookup(name)
        if info is None:
            return None

        owner = info.get("owner", "").lstrip("@")
        entry_type = info.get("type", "skill")

        if entry_type == "skill":
            url = self._registry_url(f"@{owner}/{name}.yaml")
        else:
            ver = version or info.get("latest", "1.0.0")
            url = self._registry_url(f"@{owner}/{name}/{ver}.yaml")

        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                raw = resp.read().decode()
        except urllib.error.URLError as exc:
            raise HubError(f"Failed to fetch registry file: {exc}") from exc
        result: dict[str, Any] = yaml.safe_load(raw)
        return result

    def _registry_url(self, path: str) -> str:
        """Build a URL for a registry file using the configured base."""
        return f"{self._base_url}/registry/{path}"
