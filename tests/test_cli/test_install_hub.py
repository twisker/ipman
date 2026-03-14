"""Tests for `ipman install <short-name>` — IpHub-based installation."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from ipman.cli.main import cli


SKILL_REGISTRY = {
    "type": "skill",
    "name": "web-scraper",
    "description": "Browser automation for web scraping",
    "author": "@twisker",
    "agents": {
        "claude-code": {
            "plugin": "web-scraper@twisker-plugins",
            "marketplace": "https://github.com/twisker/twisker-plugins",
        },
        "openclaw": {
            "slug": "web-scraper",
            "hub": "https://clawhub.com",
        },
    },
}

INDEX_SKILL_ENTRY = {
    "name": "web-scraper",
    "owner": "@twisker",
    "type": "skill",
    "description": "Browser automation",
    "agents": ["claude-code", "openclaw"],
}

INDEX_PKG_ENTRY = {
    "name": "frontend-toolkit",
    "owner": "@twisker",
    "type": "ip",
    "latest": "2.0.0",
    "versions": ["2.0.0", "1.0.0"],
    "description": "Frontend skills",
}

PKG_VERSION_REGISTRY = {
    "version": "2.0.0",
    "released": "2026-03-14",
    "skills": [
        {"name": "css-helper"},
        {"name": "a11y-checker"},
    ],
}


def _mock_adapter(install_ok: bool = True) -> MagicMock:
    adapter = MagicMock()
    adapter.name = "claude-code"
    adapter.display_name = "Claude Code"
    adapter.install_skill.return_value = subprocess.CompletedProcess(
        args=[], returncode=0 if install_ok else 1,
        stdout="OK\n" if install_ok else "",
        stderr="" if install_ok else "Failed",
    )
    return adapter


class TestInstallFromHub:
    """Test `ipman install <short-name>` via IpHub."""

    def test_install_skill_from_hub(self) -> None:
        """Install a skill by short name via IpHub lookup."""
        adapter = _mock_adapter()
        hub = MagicMock()
        hub.lookup.return_value = INDEX_SKILL_ENTRY
        hub.fetch_registry.return_value = SKILL_REGISTRY

        runner = CliRunner()
        with (
            patch("ipman.cli.skill._resolve_agent", return_value=adapter),
            patch("ipman.cli.skill._get_hub_client", return_value=hub),
        ):
            result = runner.invoke(cli, ["install", "web-scraper"])
        assert result.exit_code == 0, result.output
        adapter.install_skill.assert_called_once_with("web-scraper")

    def test_install_skill_not_found_in_hub(self) -> None:
        """Short name not found in IpHub should fail."""
        adapter = _mock_adapter()
        hub = MagicMock()
        hub.lookup.return_value = None

        runner = CliRunner()
        with (
            patch("ipman.cli.skill._resolve_agent", return_value=adapter),
            patch("ipman.cli.skill._get_hub_client", return_value=hub),
        ):
            result = runner.invoke(cli, ["install", "nonexistent-skill"])
        assert result.exit_code != 0

    def test_install_ip_package_from_hub(self) -> None:
        """Install an IP package by short name installs all its skills."""
        adapter = _mock_adapter()
        hub = MagicMock()
        hub.lookup.return_value = INDEX_PKG_ENTRY
        hub.fetch_registry.return_value = PKG_VERSION_REGISTRY

        runner = CliRunner()
        with (
            patch("ipman.cli.skill._resolve_agent", return_value=adapter),
            patch("ipman.cli.skill._get_hub_client", return_value=hub),
        ):
            result = runner.invoke(cli, ["install", "frontend-toolkit"])
        assert result.exit_code == 0, result.output
        assert adapter.install_skill.call_count == 2
        adapter.install_skill.assert_any_call("css-helper")
        adapter.install_skill.assert_any_call("a11y-checker")

    def test_install_hub_dry_run(self) -> None:
        """--dry-run with IpHub skill should not install."""
        adapter = _mock_adapter()
        hub = MagicMock()
        hub.lookup.return_value = INDEX_SKILL_ENTRY
        hub.fetch_registry.return_value = SKILL_REGISTRY

        runner = CliRunner()
        with (
            patch("ipman.cli.skill._resolve_agent", return_value=adapter),
            patch("ipman.cli.skill._get_hub_client", return_value=hub),
        ):
            result = runner.invoke(cli, ["install", "web-scraper", "--dry-run"])
        assert result.exit_code == 0
        adapter.install_skill.assert_not_called()
        assert "web-scraper" in result.output


class TestFetchRegistry:
    """Test IpHubClient.fetch_registry()."""

    def test_fetch_skill_registry(self, tmp_path: Path) -> None:
        """Fetch a skill's full registry file."""
        from ipman.hub.client import IpHubClient

        registry_yaml = """\
type: skill
name: web-scraper
description: "Browser automation"
agents:
  claude-code:
    plugin: "web-scraper@twisker-plugins"
"""
        client = IpHubClient(cache_dir=tmp_path)
        client._index = {
            "skills": {
                "web-scraper": {
                    "owner": "@twisker",
                    "type": "skill",
                },
            },
            "packages": {},
        }

        with patch("ipman.hub.client.urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = registry_yaml.encode()
            mock_resp.__enter__ = lambda s: s
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_resp

            result = client.fetch_registry("web-scraper")

        assert result is not None
        assert result["name"] == "web-scraper"
        assert "agents" in result

    def test_fetch_package_version_registry(self, tmp_path: Path) -> None:
        """Fetch a package's version file."""
        from ipman.hub.client import IpHubClient

        version_yaml = """\
version: "2.0.0"
skills:
  - name: css-helper
  - name: a11y-checker
"""
        client = IpHubClient(cache_dir=tmp_path)
        client._index = {
            "skills": {},
            "packages": {
                "frontend-toolkit": {
                    "owner": "@twisker",
                    "type": "ip",
                    "latest": "2.0.0",
                },
            },
        }

        with patch("ipman.hub.client.urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = version_yaml.encode()
            mock_resp.__enter__ = lambda s: s
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_resp

            result = client.fetch_registry("frontend-toolkit")

        assert result is not None
        assert result["version"] == "2.0.0"
        assert len(result["skills"]) == 2

    def test_fetch_registry_not_found(self, tmp_path: Path) -> None:
        """Nonexistent name should return None."""
        from ipman.hub.client import IpHubClient

        client = IpHubClient(cache_dir=tmp_path)
        client._index = {"skills": {}, "packages": {}}
        result = client.fetch_registry("nonexistent")
        assert result is None
