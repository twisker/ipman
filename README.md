<p align="center">
  <img src="images/IpMan.jpg" alt="IpMan Banner" width="600" />
</p>

# IpMan - Intelligence Package Manager

*I can take on ten.*

> Agent skill virtual environment manager — like conda/uv, but for AI agent skills. With built-in defense against malicious skills.

[36% of AI agent skills contain prompt injection. 824+ confirmed malicious skills exist in the wild.](https://snyk.io/blog/toxicskills-malicious-ai-agent-skills-clawhub/) IpMan doesn't just manage skills — it protects you from them.

## Why IpMan?

The AI agent skill ecosystem is the new software supply chain — and it's under attack. Skills run with **full agent permissions**, have **no sandbox by default**, and the barrier to publishing is just a Markdown file. IpMan provides:

- **Risk assessment before installation** — every skill is scanned for red flags (credential theft, data exfiltration, obfuscated code, prompt injection)
- **Four security modes** — from PERMISSIVE (install everything) to STRICT (only verified-safe skills)
- **Community-driven threat reporting** — flag suspicious skills, report counts feed back into risk scoring
- **Publish-time gatekeeping** — HIGH/EXTREME risk skills are blocked from IpHub at the door

## Features

### Security First

- **Risk Assessment Engine** — Detects credential harvesting, obfuscated code (base64/eval/exec), unauthorized network calls, sudo escalation, access to sensitive paths (~/.ssh, ~/.aws), and prompt injection patterns. Risk levels: LOW / MEDIUM / HIGH / EXTREME
- **Security Modes** — PERMISSIVE, DEFAULT, CAUTIOUS, STRICT. Control the risk tolerance for your environment
- **Smart Trust Model** — IpHub skills carry pre-assessed risk labels. Local/URL installs trigger mandatory on-device assessment. Override with `--vet` or `--no-vet`
- **Security Logging** — All blocked/warned installs are logged to `~/.ipman/security.log`
- **Community Reporting** — `ipman hub report <name>` to flag suspicious skills. Report counts are publicly visible

### Package Management

- **Virtual Environments** — Create isolated skill environments per project, user, or machine
- **IP Packages** — Bundle skills into distributable `.ip.yaml` files
- **Dependency Resolution** — Recursive dependencies with version constraints (`>=`, `^`, `~`)
- **Agent Agnostic** — Works with Claude Code, OpenClaw, and more via adapter plugins

### IpHub Registry

- **Search & Browse** — Find skills by keyword, filter by agent
- **Publish** — Submit skills/IP packages via automated GitHub PR workflow
- **Rankings** — Top skills by install count
- **Mirror Support** — Configure alternative hub URLs for regional access (CNB mirror (cnb.cool) available)

## Installation

```bash
# Via PyPI
pip install ipman-cli

# Via uv
uv pip install ipman-cli

# Via curl (Linux / macOS)
curl -sSL https://raw.githubusercontent.com/twisker/ipman/main/install.sh | bash
```

## Quick Start

```bash
# Create and activate a skill environment
ipman env create myenv
ipman env activate myenv

# Install a skill (auto-assessed for security risks)
ipman install web-scraper

# Install from a local IP package (triggers mandatory risk scan)
ipman install frontend-kit.ip.yaml

# Force risk assessment on an IpHub skill
ipman install suspicious-tool --vet

# Install in strict security mode
ipman install some-skill --security strict

# Pack current environment
ipman pack --name my-kit --version 1.0.0

# Search and publish to IpHub
ipman hub search scraper
ipman hub publish my-skill --description "My awesome skill"

# Report a suspicious skill
ipman hub report sketchy-tool --reason "Sends data to unknown server"
```

## Security Modes

| Mode | Behavior | Use case |
|------|----------|----------|
| `permissive` | Install everything, warn only on EXTREME | Trusted internal environments |
| `default` | Block EXTREME, warn on HIGH | General use |
| `cautious` | Block HIGH+EXTREME, warn on MEDIUM | Production environments |
| `strict` | Only LOW allowed; re-assess all sources locally | High-security deployments |

```bash
# Set via CLI flag
ipman install web-scraper --security cautious

# Set via config file (~/.ipman/config.yaml)
security:
  mode: cautious
```

## Configuration

IpMan reads `~/.ipman/config.yaml` for default settings:

```yaml
security:
  mode: default          # permissive | default | cautious | strict
  log_enabled: true
  log_path: ~/.ipman/security.log

hub:
  url: https://raw.githubusercontent.com/twisker/iphub/main
  # Mirror for restricted regions:
  # url: https://cnb.cool/lutuai/twisker/iphub/raw/main

agent:
  default: auto          # auto | claude-code | openclaw
```

Priority: CLI flags > environment variables (`IPMAN_HUB_URL`) > config file > defaults.

## CLI Reference

| Command | Description |
|---------|-------------|
| **Environments** | |
| `ipman env create <name>` | Create a new skill environment |
| `ipman env activate <name>` | Activate an environment |
| `ipman env deactivate` | Deactivate current environment |
| `ipman env delete <name>` | Delete an environment |
| `ipman env list` | List all environments |
| `ipman env status` | Show active environment details |
| **Skills** | |
| `ipman install <source>` | Install a skill or IP package |
| `ipman uninstall <name>` | Uninstall a skill |
| `ipman skill list` | List installed skills |
| `ipman pack` | Pack environment into .ip.yaml |
| **IpHub** | |
| `ipman hub search <query>` | Search IpHub registry |
| `ipman hub info <name>` | Show skill/package details |
| `ipman hub top` | Show most installed items |
| `ipman hub publish <source>` | Publish to IpHub |
| `ipman hub report <name>` | Report a suspicious skill |

## Architecture

```
CLI Layer (Click)
    |
Security Layer (vetter, security modes, logging)
    |
Core Layer (environment, package, resolver, config)
    |
Agent Adapter Layer (Claude Code, OpenClaw, ...)
    |
IpHub Layer (registry, search, publish, stats, mirror)
```

## Roadmap

| Phase | Focus | Status |
|-------|-------|--------|
| Phase 1 | Virtual environments + agent CLI skill management | Done |
| Phase 2 | IP package format + pack + install + dependency resolution | Done |
| Phase 3 | IpHub (search, publish, stats) | Done |
| Phase 4 | Polish, docs, PyPI release | Done |
| Phase 5 | Security (risk engine, security modes, reporting, mirrors) | Done |
| Phase 6 | Internationalization + multi-platform distribution | In Progress |

## IpHub Rankings

<!-- TOP_SKILLS_START -->
*Rankings will appear here once IpHub has install data.*
<!-- TOP_SKILLS_END -->

<!-- TOP_PACKAGES_START -->
<!-- TOP_PACKAGES_END -->

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=twisker/ipman&type=Date)](https://star-history.com/#twisker/ipman&Date)

## Development

```bash
git clone https://github.com/twisker/ipman.git
cd ipman
uv sync

uv run pytest              # 252 tests
uv run ruff check src/ tests/
uv run mypy src/ipman/
```

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.
