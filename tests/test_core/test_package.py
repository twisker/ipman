"""Tests for IP package parsing and validation."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from ipman.core.package import (
    DependencyRef,
    IPPackage,
    SkillRef,
    ValidationError,
    dump_ip_file,
    parse_ip_file,
)

# ---------------------------------------------------------------------------
# SkillRef tests
# ---------------------------------------------------------------------------

class TestSkillRef:
    """Test SkillRef data model."""

    def test_iphub_mode(self) -> None:
        ref = SkillRef(name="web-scraper")
        assert ref.name == "web-scraper"
        assert ref.source is None
        assert ref.is_direct_source is False

    def test_direct_source_mode(self) -> None:
        source = {
            "claude-code": {
                "plugin": "tool@marketplace",
            },
        }
        ref = SkillRef(name="my-tool", source=source)
        assert ref.is_direct_source is True
        assert ref.source["claude-code"]["plugin"] == "tool@marketplace"


class TestDependencyRef:
    """Test DependencyRef data model."""

    def test_iphub_mode_with_version(self) -> None:
        dep = DependencyRef(name="base-utils", version=">=1.0.0")
        assert dep.name == "base-utils"
        assert dep.version == ">=1.0.0"
        assert dep.source is None
        assert dep.is_direct_source is False

    def test_direct_source_local(self) -> None:
        dep = DependencyRef(
            name="team-kit",
            source="./team-kit.ip.yaml",
        )
        assert dep.is_direct_source is True

    def test_direct_source_url(self) -> None:
        dep = DependencyRef(
            name="shared",
            source="https://example.com/shared.ip.yaml",
        )
        assert dep.is_direct_source is True


# ---------------------------------------------------------------------------
# IPPackage tests
# ---------------------------------------------------------------------------

class TestIPPackage:
    """Test IPPackage data model."""

    def test_basic_creation(self) -> None:
        pkg = IPPackage(
            name="my-pkg",
            version="1.0.0",
            description="Test package",
            skills=[SkillRef(name="web-scraper")],
        )
        assert pkg.name == "my-pkg"
        assert pkg.version == "1.0.0"
        assert len(pkg.skills) == 1

    def test_with_dependencies(self) -> None:
        pkg = IPPackage(
            name="my-pkg",
            version="1.0.0",
            description="Test",
            skills=[],
            dependencies=[
                DependencyRef(name="base", version=">=1.0"),
            ],
        )
        assert len(pkg.dependencies) == 1


# ---------------------------------------------------------------------------
# parse_ip_file tests
# ---------------------------------------------------------------------------

MINIMAL_IP = dedent("""\
    name: test-pkg
    version: "1.0.0"
    description: "A test package"
    skills:
      - name: web-scraper
      - name: css-helper
""")

FULL_IP = dedent("""\
    name: frontend-kit
    version: "2.0.0"
    description: "Frontend development skills"
    author:
      name: "Twisker"
      github: "@twisker"
    license: MIT
    skills:
      - name: css-helper
      - name: our-tool
        description: "Internal tool"
        source:
          claude-code:
            plugin: "our-tool@our-plugins"
            marketplace: "https://github.com/ourorg/plugins"
          openclaw:
            slug: "our-tool"
            hub: "https://internal.hub"
    dependencies:
      - name: base-utils
        version: ">=1.0.0"
      - name: team-kit
        source: "./team-kit.ip.yaml"
""")

INVALID_NO_NAME = dedent("""\
    version: "1.0.0"
    description: "Missing name"
    skills: []
""")

INVALID_NO_VERSION = dedent("""\
    name: test
    description: "Missing version"
    skills: []
""")

INVALID_NO_SKILLS = dedent("""\
    name: test
    version: "1.0.0"
    description: "Missing skills"
""")


class TestParseIPFile:
    """Test IP file parsing."""

    def test_parse_minimal(self, tmp_path: Path) -> None:
        f = tmp_path / "test.ip.yaml"
        f.write_text(MINIMAL_IP)
        pkg = parse_ip_file(f)
        assert pkg.name == "test-pkg"
        assert pkg.version == "1.0.0"
        assert len(pkg.skills) == 2
        assert pkg.skills[0].name == "web-scraper"
        assert pkg.skills[1].name == "css-helper"
        assert pkg.dependencies == []

    def test_parse_full(self, tmp_path: Path) -> None:
        f = tmp_path / "full.ip.yaml"
        f.write_text(FULL_IP)
        pkg = parse_ip_file(f)
        assert pkg.name == "frontend-kit"
        assert pkg.version == "2.0.0"
        assert pkg.author == {"name": "Twisker", "github": "@twisker"}
        assert pkg.license == "MIT"
        # Skills
        assert len(pkg.skills) == 2
        assert pkg.skills[0].is_direct_source is False
        assert pkg.skills[1].is_direct_source is True
        assert pkg.skills[1].source["claude-code"]["plugin"] == "our-tool@our-plugins"
        # Dependencies
        assert len(pkg.dependencies) == 2
        assert pkg.dependencies[0].version == ">=1.0.0"
        assert pkg.dependencies[0].is_direct_source is False
        assert pkg.dependencies[1].source == "./team-kit.ip.yaml"
        assert pkg.dependencies[1].is_direct_source is True

    def test_parse_invalid_no_name(self, tmp_path: Path) -> None:
        f = tmp_path / "bad.ip.yaml"
        f.write_text(INVALID_NO_NAME)
        with pytest.raises(ValidationError, match="name"):
            parse_ip_file(f)

    def test_parse_invalid_no_version(self, tmp_path: Path) -> None:
        f = tmp_path / "bad.ip.yaml"
        f.write_text(INVALID_NO_VERSION)
        with pytest.raises(ValidationError, match="version"):
            parse_ip_file(f)

    def test_parse_invalid_no_skills(self, tmp_path: Path) -> None:
        f = tmp_path / "bad.ip.yaml"
        f.write_text(INVALID_NO_SKILLS)
        with pytest.raises(ValidationError, match="skills"):
            parse_ip_file(f)

    def test_parse_from_string(self) -> None:
        pkg = parse_ip_file(content=MINIMAL_IP)
        assert pkg.name == "test-pkg"


# ---------------------------------------------------------------------------
# dump_ip_file tests
# ---------------------------------------------------------------------------

class TestDumpIPFile:
    """Test IP file generation."""

    def test_dump_basic(self, tmp_path: Path) -> None:
        pkg = IPPackage(
            name="my-pkg",
            version="1.0.0",
            description="Test package",
            skills=[
                SkillRef(name="web-scraper"),
                SkillRef(name="css-helper"),
            ],
        )
        output = tmp_path / "out.ip.yaml"
        dump_ip_file(pkg, output)
        text = output.read_text()
        # Header comment
        assert "https://github.com/twisker/ipman" in text
        assert "ipman install" in text
        # Content
        assert "name: my-pkg" in text
        assert "web-scraper" in text

    def test_dump_roundtrip(self, tmp_path: Path) -> None:
        """Parse → dump → re-parse should preserve data."""
        f = tmp_path / "original.ip.yaml"
        f.write_text(FULL_IP)
        pkg1 = parse_ip_file(f)

        out = tmp_path / "dumped.ip.yaml"
        dump_ip_file(pkg1, out)
        pkg2 = parse_ip_file(out)

        assert pkg1.name == pkg2.name
        assert pkg1.version == pkg2.version
        assert len(pkg1.skills) == len(pkg2.skills)
        assert len(pkg1.dependencies) == len(pkg2.dependencies)

    def test_dump_with_direct_source(self, tmp_path: Path) -> None:
        pkg = IPPackage(
            name="test",
            version="1.0.0",
            description="Test",
            skills=[
                SkillRef(
                    name="private-tool",
                    source={"claude-code": {"plugin": "x@y"}},
                ),
            ],
        )
        output = tmp_path / "out.ip.yaml"
        dump_ip_file(pkg, output)
        text = output.read_text()
        assert "source:" in text
        assert "plugin:" in text
