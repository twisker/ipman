#!/usr/bin/env python3
"""Mock clawhub 0.8.0 for E2E testing (cross-platform Python script).

State dir: $MOCK_CLAWHUB_STATE (must be set by test fixture).
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path


def main() -> int:
    state = os.environ.get("MOCK_CLAWHUB_STATE", ".mock_clawhub_state")
    skills_dir = Path(state) / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)

    args = sys.argv[1:]
    if not args:
        print("error: no command specified", file=sys.stderr)
        return 1

    cmd = args[0]
    rest = args[1:]

    if cmd == "install":
        return _install(rest, skills_dir)
    if cmd == "uninstall":
        return _uninstall(rest, skills_dir)
    if cmd == "list":
        return _list(rest, skills_dir)

    print(f"error: unknown command: {cmd}", file=sys.stderr)
    return 1


def _install(args: list[str], skills_dir: Path) -> int:
    name = ""
    force = False
    workdir = ""
    i = 0
    while i < len(args):
        if args[i] == "--force":
            force = True
        elif args[i] == "--hub":
            i += 1  # skip value
        elif args[i] == "--workdir":
            i += 1
            workdir = args[i] if i < len(args) else ""
        elif not args[i].startswith("--"):
            name = args[i]
        i += 1

    if not name:
        print("error: missing skill name", file=sys.stderr)
        return 1

    target = Path(workdir) if workdir else skills_dir
    skill_path = target / name
    skill_path.mkdir(parents=True, exist_ok=True)
    (skill_path / "SKILL.md").write_text(
        f"---\nname: {name}\nversion: 1.0.0\n---\n"
        f"Mock skill installed by mock clawhub.\n",
        encoding="utf-8",
    )
    print(f"Installed {name}")
    return 0


def _uninstall(args: list[str], skills_dir: Path) -> int:
    name = ""
    yes = False
    for arg in args:
        if arg == "--yes":
            yes = True
        elif not arg.startswith("--"):
            name = arg

    if not name:
        print("error: missing skill name", file=sys.stderr)
        return 1

    if not yes:
        print("error: Pass --yes (no input)", file=sys.stderr)
        return 1

    skill_path = skills_dir / name
    if skill_path.exists():
        shutil.rmtree(skill_path)
    print(f"Uninstalled {name}")
    return 0


def _list(args: list[str], skills_dir: Path) -> int:
    if args and args[0] == "--json":
        print("error: unknown flag: --json", file=sys.stderr)
        return 1

    for d in sorted(skills_dir.iterdir()):
        if d.is_dir():
            print(f"{d.name}  1.0.0  enabled")
    return 0


if __name__ == "__main__":
    sys.exit(main())
