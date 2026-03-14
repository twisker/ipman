# Skill Management

Skills are managed through agent native CLI commands. IpMan delegates to the underlying agent tool (Claude Code, OpenClaw) for actual install/uninstall operations.

## Install

```bash
# From IpHub by short name
ipman install web-scraper

# From a local .ip.yaml file (triggers mandatory risk scan)
ipman install frontend-kit.ip.yaml

# With explicit agent
ipman install web-scraper --agent claude-code

# Preview without installing
ipman install frontend-kit.ip.yaml --dry-run

# Force local risk assessment on IpHub skill
ipman install web-scraper --vet

# Skip risk assessment on local file
ipman install trusted-kit.ip.yaml --no-vet

# Set security mode for this install
ipman install web-scraper --security cautious

# Auto-confirm security warnings
ipman install risky-tool --yes
```

## Uninstall

```bash
ipman uninstall web-scraper
```

## List

```bash
ipman skill list
ipman skill list --agent openclaw
```

Output shows skill identifier and version:

```
  agent-sdk-dev@claude-plugins-official v1.0.0
  code-review@claude-plugins-official vd5c15b861cd2
```

The skill identifier format is agent-specific (e.g., Claude Code uses `name@marketplace`).

## Agent Detection

IpMan auto-detects the agent tool used in your project directory. Override with `--agent`:

```bash
ipman install web-scraper --agent openclaw
```
