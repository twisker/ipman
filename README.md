<p align="center">
  <img src="images/IpMan.jpg" alt="IpMan Banner" width="600" />
</p>

# IpMan - Intelligence Package Manager

*I can take on ten.*

> Agent skill virtual environment manager — like conda/uv, but for AI agent skills.

IpMan solves the growing problem of skill name collisions, version conflicts, and lack of isolated environments across AI agent tools like Claude Code and OpenClaw. It provides virtual environment management, dependency resolution, and IpHub for skill distribution.

## Features

- **Virtual Environments** — Create isolated skill environments per project, user, or machine
- **Skill Management** — Install, uninstall, upgrade skills with full metadata tracking
- **IP Packages** — Bundle skills into distributable Intelligence Packages (YAML-based)
- **Agent Agnostic** — Works with Claude Code, OpenClaw, and more via adapter plugins
- **IpHub** — Search, download, and publish skills to the community
- **Cross-Platform** — Linux, macOS, Windows

## Installation

```bash
# Via PyPI
pip install ipman

# Via uv
uv pip install ipman

# Via curl (Unix-like)
curl -sSL https://raw.githubusercontent.com/twisker/ipman/main/install.sh | bash
```

## Quick Start

```bash
# Create a virtual skill environment for the current project
ipman create myenv

# Activate the environment
ipman activate myenv

# Install a skill
ipman install web-scraper

# List installed skills
ipman skill list

# Export environment as an IP package
ipman export myenv.ip.yaml

# Deactivate
ipman deactivate
```

## Architecture

```
CLI Layer (Click)
    |
Core Layer (environment, skill, package, resolver)
    |
Agent Adapter Layer (Claude Code, OpenClaw, ...)
    |
IpHub Layer (reference registry, search, publish)
```

## Module Overview

| Module | Description |
|--------|-------------|
| `ipman.cli` | Command-line interface (Click-based subcommands) |
| `ipman.core` | Core business logic — environments, skills, packages, dependency resolution |
| `ipman.agents` | Agent tool adapters (plugin architecture) |
| `ipman.hub` | IpHub client and publisher |
| `ipman.utils` | Cross-platform utilities (symlinks, i18n, agent detection) |

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ |
| Package Manager | uv |
| CLI Framework | Click |
| Testing | pytest |
| Linting | ruff |
| Type Checking | mypy |
| CI/CD | GitHub Actions |
| IP Package Format | YAML |

## Directory Structure

```
src/ipman/
├── cli/          # CLI commands
├── core/         # Business logic
├── agents/       # Agent adapters
├── hub/          # IpHub
└── utils/        # Utilities
tests/
docs/
scripts/          # Version bump scripts
```

## Roadmap

| Phase | Focus | Status |
|-------|-------|--------|
| Phase 1 | CLI skeleton + virtual environments + agent CLI skill management | In Progress (Sprint 1 done) |
| Phase 2 | IP package format + pack/unpack + dependency resolution | Planned |
| Phase 3 | IpHub (reference registry, search, publish) | Designed |
| Phase 4 | i18n, docs, Windows installer, PyPI release | Planned |

## Development

```bash
# Clone and setup
git clone https://github.com/twisker/ipman.git
cd ipman
uv sync

# Run tests
uv run pytest

# Lint
uv run ruff check src/

# Type check
uv run mypy src/
```

## Branching Strategy (Git Flow)

- `main` — Stable releases
- `dev` — Development integration
- `feature/*` — Feature branches
- `release/*` — Release preparation
- `hotfix/*` — Emergency fixes

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.
