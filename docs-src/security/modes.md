# Security Modes

IpMan provides four security mode levels to balance convenience and safety.

## Mode Comparison

| Mode | LOW | MEDIUM | HIGH | EXTREME | Use case |
|------|-----|--------|------|---------|----------|
| **PERMISSIVE** | Install | Install | Install | Warn+Install | Trusted internal networks |
| **DEFAULT** | Install | Install | Warn+Install | Block | General everyday use |
| **CAUTIOUS** | Install | Warn+Install | Block | Block | Production environments |
| **STRICT** | Install | Warn+Confirm | Block | Block | High-security deployments |

## Actions Explained

- **Install** — Silent installation, no warning
- **Warn+Install** — Display warning, log to security log, proceed
- **Warn+Confirm** — Display warning, require explicit `y/n` confirmation (bypass with `--yes`)
- **Block** — Refuse installation, display risk report, log to security log

## Setting the Mode

```bash
# Per-command
ipman install web-scraper --security cautious

# In config file (~/.ipman/config.yaml)
security:
  mode: cautious

# Default if unset: DEFAULT
```

## STRICT Mode Special Behavior

In STRICT mode, **all install sources** trigger a local risk assessment — even IpHub skills that already carry a risk label. This provides maximum protection at the cost of slower installs.
