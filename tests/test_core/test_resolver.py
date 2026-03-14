"""Tests for dependency resolver engine."""

from __future__ import annotations

import pytest

from ipman.core.resolver import (
    VersionConstraint,
    parse_constraint,
    version_matches,
    resolve_dependencies,
    CyclicDependencyError,
)


# ---------------------------------------------------------------------------
# VersionConstraint parsing
# ---------------------------------------------------------------------------

class TestParseConstraint:
    """Test version constraint string parsing."""

    def test_exact_version(self) -> None:
        c = parse_constraint("1.2.0")
        assert c.op == "=="
        assert c.major == 1
        assert c.minor == 2
        assert c.patch == 0

    def test_gte(self) -> None:
        c = parse_constraint(">=2.0.0")
        assert c.op == ">="
        assert c.major == 2

    def test_caret(self) -> None:
        c = parse_constraint("^1.3.0")
        assert c.op == "^"
        assert c.major == 1
        assert c.minor == 3

    def test_tilde(self) -> None:
        c = parse_constraint("~1.3.0")
        assert c.op == "~"
        assert c.minor == 3

    def test_two_part_version(self) -> None:
        c = parse_constraint(">=1.0")
        assert c.major == 1
        assert c.minor == 0
        assert c.patch == 0

    def test_invalid_constraint(self) -> None:
        with pytest.raises(ValueError):
            parse_constraint("not-a-version")


# ---------------------------------------------------------------------------
# Version matching
# ---------------------------------------------------------------------------

class TestVersionMatches:
    """Test version_matches(candidate, constraint)."""

    def test_exact_match(self) -> None:
        assert version_matches("1.2.0", "1.2.0") is True
        assert version_matches("1.2.1", "1.2.0") is False

    def test_gte(self) -> None:
        assert version_matches("2.0.0", ">=2.0.0") is True
        assert version_matches("3.0.0", ">=2.0.0") is True
        assert version_matches("1.9.9", ">=2.0.0") is False

    def test_caret(self) -> None:
        # ^1.3.0 means >=1.3.0, <2.0.0
        assert version_matches("1.3.0", "^1.3.0") is True
        assert version_matches("1.9.9", "^1.3.0") is True
        assert version_matches("2.0.0", "^1.3.0") is False
        assert version_matches("1.2.9", "^1.3.0") is False

    def test_caret_zero_major(self) -> None:
        # ^0.2.0 means >=0.2.0, <0.3.0
        assert version_matches("0.2.0", "^0.2.0") is True
        assert version_matches("0.2.5", "^0.2.0") is True
        assert version_matches("0.3.0", "^0.2.0") is False

    def test_tilde(self) -> None:
        # ~1.3.0 means >=1.3.0, <1.4.0
        assert version_matches("1.3.0", "~1.3.0") is True
        assert version_matches("1.3.5", "~1.3.0") is True
        assert version_matches("1.4.0", "~1.3.0") is False
        assert version_matches("1.2.9", "~1.3.0") is False

    def test_none_constraint_matches_all(self) -> None:
        assert version_matches("999.0.0", None) is True


# ---------------------------------------------------------------------------
# Dependency resolution
# ---------------------------------------------------------------------------

class TestResolveDependencies:
    """Test recursive dependency resolution with cycle detection."""

    def test_no_dependencies(self) -> None:
        """Package with no dependencies returns just its own skills."""
        def fetcher(name: str, version: str | None) -> dict:
            return {
                "version": "1.0.0",
                "skills": [{"name": "skill-a"}],
                "dependencies": [],
            }

        skills = resolve_dependencies("root-pkg", None, fetcher)
        assert [s["name"] for s in skills] == ["skill-a"]

    def test_simple_dependency(self) -> None:
        """Package A depends on package B."""
        def fetcher(name: str, version: str | None) -> dict:
            if name == "pkg-a":
                return {
                    "version": "1.0.0",
                    "skills": [{"name": "skill-a"}],
                    "dependencies": [{"name": "pkg-b", "version": ">=1.0.0"}],
                }
            return {
                "version": "1.0.0",
                "skills": [{"name": "skill-b"}],
                "dependencies": [],
            }

        skills = resolve_dependencies("pkg-a", None, fetcher)
        names = [s["name"] for s in skills]
        assert "skill-a" in names
        assert "skill-b" in names

    def test_transitive_dependencies(self) -> None:
        """A -> B -> C, all skills collected."""
        def fetcher(name: str, version: str | None) -> dict:
            if name == "a":
                return {
                    "version": "1.0.0",
                    "skills": [{"name": "sa"}],
                    "dependencies": [{"name": "b"}],
                }
            if name == "b":
                return {
                    "version": "1.0.0",
                    "skills": [{"name": "sb"}],
                    "dependencies": [{"name": "c"}],
                }
            return {
                "version": "1.0.0",
                "skills": [{"name": "sc"}],
                "dependencies": [],
            }

        skills = resolve_dependencies("a", None, fetcher)
        names = [s["name"] for s in skills]
        assert names == ["sa", "sb", "sc"]

    def test_diamond_dependency(self) -> None:
        """A -> B, A -> C, both B and C -> D. D skills appear only once."""
        def fetcher(name: str, version: str | None) -> dict:
            if name == "a":
                return {
                    "version": "1.0.0",
                    "skills": [{"name": "sa"}],
                    "dependencies": [{"name": "b"}, {"name": "c"}],
                }
            if name == "b":
                return {
                    "version": "1.0.0",
                    "skills": [{"name": "sb"}],
                    "dependencies": [{"name": "d"}],
                }
            if name == "c":
                return {
                    "version": "1.0.0",
                    "skills": [{"name": "sc"}],
                    "dependencies": [{"name": "d"}],
                }
            return {
                "version": "1.0.0",
                "skills": [{"name": "sd"}],
                "dependencies": [],
            }

        skills = resolve_dependencies("a", None, fetcher)
        names = [s["name"] for s in skills]
        # sd should appear only once (deduplication)
        assert names.count("sd") == 1
        assert len(names) == 4

    def test_cyclic_dependency_detected(self) -> None:
        """A -> B -> A should raise CyclicDependencyError."""
        def fetcher(name: str, version: str | None) -> dict:
            if name == "a":
                return {
                    "version": "1.0.0",
                    "skills": [{"name": "sa"}],
                    "dependencies": [{"name": "b"}],
                }
            return {
                "version": "1.0.0",
                "skills": [{"name": "sb"}],
                "dependencies": [{"name": "a"}],
            }

        with pytest.raises(CyclicDependencyError):
            resolve_dependencies("a", None, fetcher)

    def test_self_dependency_detected(self) -> None:
        """Package depending on itself should raise CyclicDependencyError."""
        def fetcher(name: str, version: str | None) -> dict:
            return {
                "version": "1.0.0",
                "skills": [{"name": "s"}],
                "dependencies": [{"name": "a"}],
            }

        with pytest.raises(CyclicDependencyError):
            resolve_dependencies("a", None, fetcher)

    def test_skill_deduplication(self) -> None:
        """Same skill name from different packages should be deduplicated."""
        def fetcher(name: str, version: str | None) -> dict:
            if name == "a":
                return {
                    "version": "1.0.0",
                    "skills": [{"name": "shared-skill"}, {"name": "sa"}],
                    "dependencies": [{"name": "b"}],
                }
            return {
                "version": "1.0.0",
                "skills": [{"name": "shared-skill"}, {"name": "sb"}],
                "dependencies": [],
            }

        skills = resolve_dependencies("a", None, fetcher)
        names = [s["name"] for s in skills]
        assert names.count("shared-skill") == 1
