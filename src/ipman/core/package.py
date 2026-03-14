"""IP package data models, parsing, and serialization."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class ValidationError(Exception):
    """Raised when an IP file fails validation."""


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class SkillRef:
    """Reference to a skill in an IP package."""

    name: str
    version: str | None = None
    source: dict[str, Any] | None = None
    description: str | None = None

    @property
    def is_direct_source(self) -> bool:
        return self.source is not None


@dataclass
class DependencyRef:
    """Reference to a dependency IP package."""

    name: str
    version: str | None = None
    source: str | None = None

    @property
    def is_direct_source(self) -> bool:
        return self.source is not None


@dataclass
class IPPackage:
    """Parsed representation of an .ip.yaml file."""

    name: str
    version: str
    description: str
    skills: list[SkillRef]
    dependencies: list[DependencyRef] = field(default_factory=list)
    author: dict[str, str] | None = None
    license: str | None = None


# ---------------------------------------------------------------------------
# Name validation
# ---------------------------------------------------------------------------

_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9\-]{1,48}[a-z0-9]$")


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def parse_ip_file(
    path: Path | None = None,
    *,
    content: str | None = None,
) -> IPPackage:
    """Parse an .ip.yaml file into an IPPackage.

    Provide either *path* (reads from disk) or *content* (raw YAML string).
    """
    if content is None:
        if path is None:
            msg = "Either path or content must be provided"
            raise ValueError(msg)
        content = path.read_text(encoding="utf-8")

    data = yaml.safe_load(content)
    if not isinstance(data, dict):
        msg = "IP file must be a YAML mapping"
        raise ValidationError(msg)

    # --- required fields ---
    if "name" not in data:
        msg = "Missing required field: name"
        raise ValidationError(msg)
    if "version" not in data:
        msg = "Missing required field: version"
        raise ValidationError(msg)
    if "skills" not in data:
        msg = "Missing required field: skills"
        raise ValidationError(msg)

    # --- skills ---
    raw_skills: list[dict[str, Any]] = data.get("skills") or []
    skills = [
        SkillRef(
            name=s["name"],
            version=s.get("version"),
            source=s.get("source"),
            description=s.get("description"),
        )
        for s in raw_skills
    ]

    # --- dependencies ---
    raw_deps: list[dict[str, Any]] = data.get("dependencies") or []
    dependencies = [
        DependencyRef(
            name=d["name"],
            version=d.get("version"),
            source=d.get("source"),
        )
        for d in raw_deps
    ]

    return IPPackage(
        name=data["name"],
        version=str(data["version"]),
        description=data.get("description", ""),
        skills=skills,
        dependencies=dependencies,
        author=data.get("author"),
        license=data.get("license"),
    )


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

_HEADER = """\
# IpMan Intelligence Package — https://github.com/twisker/ipman
# Install: ipman install {filename}
"""


def dump_ip_file(pkg: IPPackage, path: Path) -> None:
    """Serialize an IPPackage to an .ip.yaml file with header comment."""
    data: dict[str, Any] = {
        "name": pkg.name,
        "version": pkg.version,
        "description": pkg.description,
    }

    if pkg.author:
        data["author"] = pkg.author
    if pkg.license:
        data["license"] = pkg.license

    # Skills
    skills_out: list[dict[str, Any]] = []
    for s in pkg.skills:
        entry: dict[str, Any] = {"name": s.name}
        if s.version:
            entry["version"] = s.version
        if s.description:
            entry["description"] = s.description
        if s.source:
            entry["source"] = s.source
        skills_out.append(entry)
    data["skills"] = skills_out

    # Dependencies
    if pkg.dependencies:
        deps_out: list[dict[str, Any]] = []
        for d in pkg.dependencies:
            dep_entry: dict[str, Any] = {"name": d.name}
            if d.version:
                dep_entry["version"] = d.version
            if d.source:
                dep_entry["source"] = d.source
            deps_out.append(dep_entry)
        data["dependencies"] = deps_out

    header = _HEADER.format(filename=path.name)
    body = yaml.dump(
        data, default_flow_style=False, allow_unicode=True, sort_keys=False,
    )
    path.write_text(header + "\n" + body, encoding="utf-8")
