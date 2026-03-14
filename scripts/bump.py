#!/usr/bin/env python3
"""Cross-platform version bump script.

Usage:
    python scripts/bump.py patch   # 0.1.2 → 0.1.3 (auto by pre-commit)
    python scripts/bump.py minor   # 0.1.2 → 0.2.0
    python scripts/bump.py major   # 0.1.2 → 1.0.0
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def get_repo_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, check=True,
    )
    return Path(result.stdout.strip())


def bump(level: str) -> None:
    version_file = get_repo_root() / "VERSION"

    if not version_file.exists():
        version_file.write_text("0.1.0\n")

    version = version_file.read_text().strip()
    parts = version.split(".")
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])

    if level == "patch":
        patch += 1
    elif level == "minor":
        minor += 1
        patch = 0
    elif level == "major":
        major += 1
        minor = 0
        patch = 0
    else:
        print(f"Unknown level: {level}")
        print("Usage: python scripts/bump.py [patch|minor|major]")
        sys.exit(1)

    new_version = f"{major}.{minor}.{patch}"
    version_file.write_text(new_version + "\n")

    subprocess.run(["git", "add", str(version_file)], check=True)
    print(f"Version bumped: {version} -> {new_version}")


if __name__ == "__main__":
    level = sys.argv[1] if len(sys.argv) > 1 else "patch"
    bump(level)
