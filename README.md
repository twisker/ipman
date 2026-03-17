<p align="center">
  <img src="images/IpMan.jpg" alt="IpMan Banner" width="600" />
</p>

# IpMan - Intelligence Package Manager

*I can take on ten.*

> Agent skill virtual environment manager — like conda/uv, but for AI agent skills. With built-in defense against malicious skills.

**[Documentation](https://twisker.github.io/ipman)** | **[中文文档](https://twisker.github.io/ipman/zh/)** | **[中文 README](README.zh-cn.md)**

---

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
- **Mirror Support** — Configure alternative hub URLs for regional access (CNB mirror available)

## Installation

```bash
# Via PyPI
pip install ipman-cli

# Via uv
uv pip install ipman-cli

# Via curl (Linux / macOS)
curl -sSL https://raw.githubusercontent.com/twisker/ipman/main/install.sh | bash
```

Pre-built binaries for Windows/macOS/Linux are available on [GitHub Releases](https://github.com/twisker/ipman/releases).

## Quick Start

```bash
# Create and activate a skill environment
ipman env create myenv
ipman env activate myenv

# Install a skill (auto-assessed for security risks)
ipman install web-scraper

# Install from a local IP package (triggers mandatory risk scan)
ipman install frontend-kit.ip.yaml

# Pack current environment
ipman pack --name my-kit --version 1.0.0

# Search and publish to IpHub
ipman hub search scraper
ipman hub publish my-skill --description "My awesome skill"

# Report a suspicious skill
ipman hub report sketchy-tool --reason "Sends data to unknown server"
```

For the full guide, see the **[Documentation](https://twisker.github.io/ipman)**.

## Security Modes

| Mode | Behavior | Use case |
|------|----------|----------|
| `permissive` | Install everything, warn only on EXTREME | Trusted internal environments |
| `default` | Block EXTREME, warn on HIGH | General use |
| `cautious` | Block HIGH+EXTREME, warn on MEDIUM | Production environments |
| `strict` | Only LOW allowed; re-assess all sources locally | High-security deployments |

See the **[Security Guide](https://twisker.github.io/ipman/guide/security/)** for details.

## IpHub Rankings

<!-- TOP_SKILLS_START -->
## Top 10 Skills

*Updated: 2026-03-17T04:20:56Z*

| # | Name | Type | Installs | Users |
|---|------|------|----------|-------|
<!-- TOP_SKILLS_END -->

<!-- TOP_PACKAGES_START -->
## Top 10 Packages

*Updated: 2026-03-17T04:20:56Z*

| # | Name | Type | Installs | Users |
|---|------|------|----------|-------|
<!-- TOP_PACKAGES_END -->

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=twisker/ipman&type=Date)](https://star-history.com/#twisker/ipman&Date)

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.
