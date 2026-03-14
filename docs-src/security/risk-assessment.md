# Risk Assessment Engine

IpMan's risk assessment engine analyzes skills before installation, inspired by [Skill Vetter](https://clawhub.ai/spclaudehome/skill-vetter).

## What It Checks

### Red Flags (auto-elevate to HIGH/EXTREME)

- Network requests to unknown URLs or raw IP addresses
- Credential harvesting (API keys, tokens)
- Access to sensitive paths (`~/.ssh`, `~/.aws`, `~/.config`)
- Access to agent memory files (`MEMORY.md`, `SOUL.md`)
- Obfuscated code (base64 encoding, minified code, dynamic evaluation)
- Elevated privilege requests (sudo/root)
- Outbound data exfiltration patterns

### Permission Scope

- File read/write scope
- Network call targets
- Command execution
- Scope minimality (Principle of Least Privilege)

### Source Reputation

- Author publish history
- Download/install count
- Repository age and stars
- Community reports

## Risk Report Output

```
SKILL VETTING REPORT
===================================================
Skill: sketchy-tool
Source: https://example.com/sketchy.ip.yaml
---------------------------------------------------
RED FLAGS:
  - Accesses ~/.ssh/id_rsa
  - Network call to raw IP address
  - Obfuscated code in install script

PERMISSIONS:
  - Files: ~/.ssh (READ)
  - Network: external endpoint on port 8080
  - Commands: network tools, encoding tools
---------------------------------------------------
RISK LEVEL: EXTREME
VERDICT: DO NOT INSTALL
===================================================
```
