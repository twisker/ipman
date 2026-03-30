#!/usr/bin/env python3
"""Mock openclaw CLI for e2e tests."""
import sys

def main():
    args = sys.argv[1:]
    if not args:
        print("openclaw mock", file=sys.stderr)
        sys.exit(1)

    subcmd = args[0]
    if subcmd == "skills":
        handle_skills(args[1:])
    elif subcmd == "plugins":
        handle_plugins(args[1:])
    else:
        print(f"Unknown command: {subcmd}", file=sys.stderr)
        sys.exit(1)

def handle_skills(args):
    if not args:
        print("Usage: openclaw skills <command>")
        return
    cmd = args[0]
    if cmd == "list":
        print("mock-skill-a")
        print("mock-skill-b")
    elif cmd == "install":
        name = args[1] if len(args) > 1 else "unknown"
        print(f"Installed skill: {name}")
    elif cmd == "--help":
        print("openclaw skills: manage skills")
    else:
        print(f"openclaw skills {cmd}: OK")

def handle_plugins(args):
    if not args:
        print("Usage: openclaw plugins <command>")
        return
    cmd = args[0]
    if cmd == "list":
        print("mock-plugin-a")
    elif cmd == "install":
        name = args[1] if len(args) > 1 else "unknown"
        print(f"Installed plugin: {name}")
    elif cmd == "--help":
        print("openclaw plugins: manage plugins")
    else:
        print(f"openclaw plugins {cmd}: OK")

if __name__ == "__main__":
    main()
