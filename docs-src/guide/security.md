# Security Guide

IpMan includes built-in defense against malicious AI agent skills.

## Why This Matters

- 36% of ClawHub skills contain prompt injection ([Snyk ToxicSkills](https://snyk.io/blog/toxicskills-malicious-ai-agent-skills-clawhub/))
- Skills run with full agent permissions, no sandbox by default
- Attack vectors: credential theft, data exfiltration, obfuscated code execution

## Risk Levels

| Level | Meaning | Examples |
|-------|---------|----------|
| LOW | No issues detected | Notes, formatting, weather |
| MEDIUM | Some concerns | File operations, API calls |
| HIGH | Red flags detected | Credential access, system modification |
| EXTREME | Likely malicious | Root access, data exfiltration |

## Security Modes

```bash
ipman install web-scraper --security strict
```

| Mode | LOW | MEDIUM | HIGH | EXTREME |
|------|-----|--------|------|---------|
| `permissive` | Install | Install | Install | Warn |
| `default` | Install | Install | Warn | Block |
| `cautious` | Install | Warn | Block | Block |
| `strict` | Install | Confirm | Block | Block |

Set default mode in `~/.ipman/config.yaml`:

```yaml
security:
  mode: cautious
```

## Trust Model

| Source | Default behavior |
|--------|-----------------|
| IpHub | Trust existing risk label |
| Local `.ip.yaml` file | Mandatory local scan |
| URL / custom hub | Mandatory local scan |

Override with flags:

```bash
ipman install hub-skill --vet        # Force local re-scan
ipman install local.ip.yaml --no-vet # Skip local scan
```

## Security Log

Blocked and warned installs are logged to `~/.ipman/security.log`:

```
2026-03-14T10:30:00Z BLOCKED sketchy-tool source=iphub risk=EXTREME reason="credential harvesting detected"
```

Disable via config:

```yaml
security:
  log_enabled: false
```

## Report Suspicious Skills

```bash
ipman hub report sketchy-tool --reason "Accesses ~/.ssh without clear purpose"
```

Report counts feed back into risk scoring and are displayed in `ipman hub info`.
