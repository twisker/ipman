# Skill Management

Skills are managed through agent native CLI commands. IpMan delegates to the underlying agent tool (Claude Code, OpenClaw) for actual install/uninstall operations.

## Install

```bash
# From IpHub by short name
ipman install web-scraper

# From a local .ip.yaml file
ipman install frontend-kit.ip.yaml

# With explicit agent
ipman install web-scraper --agent claude-code

# Preview without installing
ipman install frontend-kit.ip.yaml --dry-run

# Force local risk assessment on IpHub skill
ipman install web-scraper --vet
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

## Agent Detection

IpMan auto-detects the agent tool used in your project directory. Override with `--agent`:

```bash
ipman install web-scraper --agent openclaw
```
