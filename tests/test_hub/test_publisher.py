"""Tests for IpHub publisher engine."""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from ipman.hub.publisher import (
    IpHubPublisher,
    PublishError,
    generate_package_registry,
    generate_skill_registry,
    generate_version_data,
    get_github_username,
)

# ---------------------------------------------------------------------------
# GitHub identity
# ---------------------------------------------------------------------------

class TestGetGitHubUsername:
    """Test GitHub username detection via gh CLI."""

    @patch("ipman.hub.publisher.subprocess.run")
    def test_get_username(self, mock_run: MagicMock) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="twisker\n", stderr="",
        )
        assert get_github_username() == "twisker"

    @patch("ipman.hub.publisher.subprocess.run")
    def test_get_username_failure(self, mock_run: MagicMock) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="not logged in",
        )
        with pytest.raises(PublishError, match="GitHub"):
            get_github_username()


# ---------------------------------------------------------------------------
# Registry file generation
# ---------------------------------------------------------------------------

class TestGenerateSkillRegistry:
    """Test skill registry YAML generation."""

    def test_basic_skill(self) -> None:
        result = generate_skill_registry(
            name="web-scraper",
            description="Browser automation",
            author="@twisker",
            license_="MIT",
            agents={
                "claude-code": {
                    "plugin": "web-scraper@twisker-plugins",
                },
            },
        )
        assert result["type"] == "skill"
        assert result["name"] == "web-scraper"
        assert result["author"] == "@twisker"
        assert result["agents"]["claude-code"]["plugin"] == "web-scraper@twisker-plugins"

    def test_skill_with_keywords(self) -> None:
        result = generate_skill_registry(
            name="test",
            description="Test skill",
            author="@alice",
            keywords=["testing", "qa"],
        )
        # keywords migrated to tags field
        assert result["tags"] == ["testing", "qa"]


class TestGeneratePackageRegistry:
    """Test IP package registry file generation."""

    def test_meta_file(self) -> None:
        meta = generate_package_registry(
            name="frontend-toolkit",
            description="Frontend skills",
            author="@twisker",
            license_="MIT",
        )
        assert meta["type"] == "ip"
        assert meta["name"] == "frontend-toolkit"

    def test_version_data(self) -> None:
        from ipman.core.package import DependencyRef, IPPackage, SkillRef

        pkg = IPPackage(
            name="frontend-toolkit",
            version="2.0.0",
            description="Frontend skills",
            skills=[
                SkillRef(name="css-helper"),
                SkillRef(name="a11y-checker"),
            ],
            dependencies=[
                DependencyRef(name="base-utils", version=">=1.0.0"),
            ],
        )
        from ipman.hub.publisher import generate_version_data
        data = generate_version_data(pkg)
        assert data["version"] == "2.0.0"
        assert len(data["skills"]) == 2
        assert data["skills"][0]["name"] == "css-helper"
        assert len(data["dependencies"]) == 1


# ---------------------------------------------------------------------------
# Publisher flow
# ---------------------------------------------------------------------------

class TestIpHubPublisher:
    """Test the publish workflow (fork → create file → PR)."""

    @patch("ipman.hub.publisher.subprocess.run")
    def test_ensure_fork_contributor(self, mock_run: MagicMock) -> None:
        """Non-owner should call gh repo fork."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="alice/iphub\n", stderr="",
        )
        publisher = IpHubPublisher(username="alice")
        publisher.ensure_fork()
        assert any(
            "fork" in str(c) for c in mock_run.call_args_list
        )

    def test_ensure_fork_owner_skips(self) -> None:
        """Owner should skip fork (can't fork own repo)."""
        publisher = IpHubPublisher(username="twisker")
        # Should not raise, just return
        publisher.ensure_fork()

    @patch("ipman.hub.publisher.subprocess.run")
    def test_publish_skill_owner(self, mock_run: MagicMock) -> None:
        """Owner publish: skip fork, push directly to main repo."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="OK\n", stderr="",
        )
        publisher = IpHubPublisher(username="twisker")
        publisher.publish_skill(
            name="web-scraper",
            description="Browser automation",
            agents={
                "claude-code": {"plugin": "web-scraper@twisker-plugins"},
            },
        )
        # Should have made gh calls (branch + push + PR, no fork)
        assert mock_run.call_count >= 3  # branch + push + PR
        # No fork call
        assert not any(
            "fork" in str(c) for c in mock_run.call_args_list
        )

    @patch("ipman.hub.publisher.subprocess.run")
    def test_publish_skill_contributor(self, mock_run: MagicMock) -> None:
        """Contributor publish: fork + push to fork + PR."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="OK\n", stderr="",
        )
        publisher = IpHubPublisher(username="alice")
        publisher.publish_skill(
            name="web-scraper",
            description="Browser automation",
        )
        assert mock_run.call_count >= 4  # fork + branch + push + PR
        assert any(
            "fork" in str(c) for c in mock_run.call_args_list
        )

    @patch("ipman.hub.publisher.subprocess.run")
    def test_publish_skill_gh_failure(self, mock_run: MagicMock) -> None:
        """gh CLI failure should raise PublishError."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="permission denied",
        )
        # Use non-owner so ensure_fork actually calls gh
        publisher = IpHubPublisher(username="alice")
        with pytest.raises(PublishError):
            publisher.ensure_fork()

    @patch("ipman.hub.publisher.subprocess.run")
    def test_publish_package(self, mock_run: MagicMock) -> None:
        """Full IP package publish flow."""
        from ipman.core.package import IPPackage, SkillRef

        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="OK\n", stderr="",
        )
        pkg = IPPackage(
            name="my-toolkit",
            version="1.0.0",
            description="My toolkit",
            skills=[SkillRef(name="skill-a")],
        )
        publisher = IpHubPublisher(username="twisker")
        publisher.publish_package(pkg)
        assert mock_run.call_count >= 3


# ---------------------------------------------------------------------------
# New fields: tags, summary, changelog
# ---------------------------------------------------------------------------


def test_generate_package_registry_with_new_fields():
    result = generate_package_registry(
        name="test-pkg", description="Test", author="@tester",
        tags=["ai", "coding"], summary="A summary",
        repository="https://github.com/test/repo",
        icon="https://example.com/icon.png",
        links=[{"title": "Guide", "url": "https://example.com"}],
    )
    assert result["tags"] == ["ai", "coding"]
    assert result["summary"] == "A summary"
    assert result["repository"] == "https://github.com/test/repo"
    assert result["icon"] == "https://example.com/icon.png"
    assert result["links"] == [{"title": "Guide", "url": "https://example.com"}]


def test_generate_skill_registry_with_tags():
    result = generate_skill_registry(
        name="test-skill", description="Test", author="@tester",
        tags=["css", "layout"], summary="A CSS helper",
    )
    assert result["tags"] == ["css", "layout"]
    assert result["summary"] == "A CSS helper"


def test_generate_skill_registry_keywords_fallback():
    """keywords used as fallback when tags not provided."""
    result = generate_skill_registry(
        name="test-skill", description="Test", author="@tester",
        keywords=["old-tag"],
    )
    assert result["tags"] == ["old-tag"]


def test_generate_skill_registry_tags_over_keywords():
    """tags takes precedence over keywords."""
    result = generate_skill_registry(
        name="test-skill", description="Test", author="@tester",
        keywords=["old"], tags=["new"],
    )
    assert result["tags"] == ["new"]


def test_generate_version_data_with_changelog():
    from ipman.core.package import IPPackage, SkillRef
    pkg = IPPackage(
        name="test", version="2.0.0", description="Test",
        skills=[SkillRef(name="s1")],
    )
    changelog = {
        "summary": "Added new skill",
        "added": ["s1"],
    }
    result = generate_version_data(pkg, changelog=changelog)
    assert result["changelog"]["summary"] == "Added new skill"
    assert result["changelog"]["added"] == ["s1"]


def test_generate_version_data_without_changelog():
    from ipman.core.package import IPPackage, SkillRef
    pkg = IPPackage(
        name="test", version="1.0.0", description="Test",
        skills=[SkillRef(name="s1")],
    )
    result = generate_version_data(pkg)
    assert "changelog" not in result
