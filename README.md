<p align="center">
  <img src="images/IpMan.jpg" alt="IpMan Banner" width="600" />
</p>

# IpMan - Intelligence Package Manager

*I can take on ten.*

> Agent skill virtual environment manager — like conda/uv, but for AI agent skills.

IpMan solves the growing problem of skill name collisions, version conflicts, and lack of isolated environments across AI agent tools like Claude Code and OpenClaw. It provides virtual environment management, dependency resolution, and IpHub for skill distribution.

## Features

- **Virtual Environments** — Create isolated skill environments per project, user, or machine
- **Skill Management** — Install, uninstall, list skills via agent native CLI
- **IP Packages** — Bundle skills into distributable `.ip.yaml` files
- **Dependency Resolution** — Recursive dependencies with version constraints (`>=`, `^`, `~`)
- **Agent Agnostic** — Works with Claude Code, OpenClaw, and more via adapter plugins
- **IpHub** — Search, browse, and publish skills to the community registry
- **Cross-Platform** — Linux, macOS, Windows

## Installation

```bash
# Via PyPI
pip install ipman

# Via uv
uv pip install ipman
```

## Quick Start

```bash
# Create a virtual skill environment for the current project
ipman env create myenv

# Activate the environment
ipman env activate myenv

# Install a skill from IpHub
ipman install web-scraper

# Install from a local IP package file
ipman install frontend-kit.ip.yaml

# List installed skills
ipman skill list

# Pack current environment into an IP file
ipman pack --name my-kit --version 1.0.0

# Search IpHub
ipman hub search scraper

# Publish a skill to IpHub
ipman hub publish my-skill --description "My awesome skill"

# Deactivate
ipman env deactivate
```

## CLI Reference

| Command | Description |
|---------|-------------|
| `ipman env create <name>` | Create a new skill environment |
| `ipman env activate <name>` | Activate an environment |
| `ipman env deactivate` | Deactivate current environment |
| `ipman env delete <name>` | Delete an environment |
| `ipman env list` | List all environments |
| `ipman env status` | Show active environment details |
| `ipman install <source>` | Install a skill or IP package |
| `ipman uninstall <name>` | Uninstall a skill |
| `ipman skill list` | List installed skills |
| `ipman pack` | Pack environment into .ip.yaml |
| `ipman hub search <query>` | Search IpHub registry |
| `ipman hub info <name>` | Show skill/package details |
| `ipman hub top` | Show most installed items |
| `ipman hub publish <source>` | Publish to IpHub |

## Architecture

```
CLI Layer (Click)
    |
Core Layer (environment, package, resolver)
    |
Agent Adapter Layer (Claude Code, OpenClaw, ...)
    |
IpHub Layer (reference registry, search, publish)
```

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ |
| Package Manager | uv |
| CLI Framework | Click |
| Testing | pytest (176 tests) |
| Linting | ruff |
| Type Checking | mypy (strict) |
| CI/CD | GitHub Actions |
| IP Package Format | YAML |

## Roadmap

| Phase | Focus | Status |
|-------|-------|--------|
| Phase 1 | Virtual environments + agent CLI skill management | Done |
| Phase 2 | IP package format + pack + install + dependency resolution | Done |
| Phase 3 | IpHub (search, publish, stats) | Done |
| Phase 4 | Polish, docs, PyPI release | In Progress |

## Development

```bash
# Clone and setup
git clone https://github.com/twisker/ipman.git
cd ipman
uv sync

# Run tests
uv run pytest

# Lint
uv run ruff check src/ tests/

# Type check
uv run mypy src/ipman/
```

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.
