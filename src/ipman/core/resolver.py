"""Dependency resolver — version matching, recursive resolution."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class CyclicDependencyError(Exception):
    """Raised when a cyclic dependency is detected."""


# ---------------------------------------------------------------------------
# Version constraint
# ---------------------------------------------------------------------------

_CONSTRAINT_RE = re.compile(
    r"^(?P<op>>=|\^|~)?(?P<major>\d+)\.(?P<minor>\d+)(?:\.(?P<patch>\d+))?$"
)


@dataclass(frozen=True)
class VersionConstraint:
    """Parsed version constraint."""

    op: str  # "==", ">=", "^", "~"
    major: int
    minor: int
    patch: int


def parse_constraint(spec: str) -> VersionConstraint:
    """Parse a version constraint string like '>=1.2.0', '^1.3.0', '~1.3.0', '1.2.0'."""
    m = _CONSTRAINT_RE.match(spec.strip())
    if not m:
        msg = f"Invalid version constraint: '{spec}'"
        raise ValueError(msg)
    op = m.group("op") or "=="
    return VersionConstraint(
        op=op,
        major=int(m.group("major")),
        minor=int(m.group("minor")),
        patch=int(m.group("patch") or 0),
    )


def _parse_version(version: str) -> tuple[int, int, int]:
    """Parse a plain version string into (major, minor, patch)."""
    parts = version.strip().split(".")
    major = int(parts[0])
    minor = int(parts[1]) if len(parts) > 1 else 0
    patch = int(parts[2]) if len(parts) > 2 else 0
    return major, minor, patch


def version_matches(candidate: str, constraint: str | None) -> bool:
    """Check if *candidate* version satisfies *constraint*.

    Returns True if constraint is None (no restriction).
    """
    if constraint is None:
        return True

    c = parse_constraint(constraint)
    v_major, v_minor, v_patch = _parse_version(candidate)
    v = (v_major, v_minor, v_patch)
    base = (c.major, c.minor, c.patch)

    if c.op == "==":
        return v == base

    if c.op == ">=":
        return v >= base

    if c.op == "^":
        # ^M.N.P  =>  >=M.N.P, <(M+1).0.0   (when M>0)
        #             >=0.N.P, <0.(N+1).0     (when M==0)
        if v < base:
            return False
        if c.major == 0:
            return v_major == 0 and v_minor == c.minor
        return v_major == c.major

    if c.op == "~":
        # ~M.N.P  =>  >=M.N.P, <M.(N+1).0
        if v < base:
            return False
        return v_major == c.major and v_minor == c.minor

    return False


# ---------------------------------------------------------------------------
# Dependency resolution
# ---------------------------------------------------------------------------

# Type alias for the fetcher callback:
#   fetcher(name, version_constraint) -> dict with keys: version, skills, dependencies
PackageFetcher = Callable[[str, str | None], dict[str, Any]]


def resolve_dependencies(
    name: str,
    version: str | None,
    fetcher: PackageFetcher,
) -> list[dict[str, Any]]:
    """Recursively resolve all skills from a package and its dependencies.

    Args:
        name: Root package name.
        version: Version constraint for the root (or None).
        fetcher: Callback that returns package data given (name, version).
                 Must return dict with 'skills' and 'dependencies' keys.

    Returns:
        Deduplicated list of skill dicts (order: root-first DFS).

    Raises:
        CyclicDependencyError: If a dependency cycle is detected.
    """
    seen_skills: set[str] = set()
    result: list[dict[str, Any]] = []
    visiting: set[str] = set()  # cycle detection (DFS stack)
    visited: set[str] = set()   # already fully resolved

    def _visit(pkg_name: str, pkg_version: str | None) -> None:
        if pkg_name in visiting:
            raise CyclicDependencyError(
                f"Cyclic dependency detected: {pkg_name}"
            )
        if pkg_name in visited:
            return

        visiting.add(pkg_name)

        data = fetcher(pkg_name, pkg_version)

        # Collect skills (deduplicate by name)
        for skill in data.get("skills", []):
            sname = skill["name"]
            if sname not in seen_skills:
                seen_skills.add(sname)
                result.append(skill)

        # Recurse into dependencies
        for dep in data.get("dependencies", []):
            dep_name = dep.get("name") or dep
            dep_version = dep.get("version") if isinstance(dep, dict) else None
            _visit(dep_name, dep_version)

        visiting.discard(pkg_name)
        visited.add(pkg_name)

    _visit(name, version)
    return result
