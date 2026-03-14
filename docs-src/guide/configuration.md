# Configuration

IpMan reads defaults from `~/.ipman/config.yaml`.

## Full Example

```yaml
security:
  mode: default          # permissive | default | cautious | strict
  log_enabled: true
  log_path: ~/.ipman/security.log

hub:
  url: https://raw.githubusercontent.com/twisker/iphub/main
  # CODING mirror (coding.net):
  # url: https://twisker.coding.net/twisker/iphub/raw/main

agent:
  default: auto          # auto | claude-code | openclaw
```

## Priority Order

1. CLI flags (`--security strict`, `--hub-url ...`)
2. Environment variables (`IPMAN_HUB_URL`)
3. Config file (`~/.ipman/config.yaml`)
4. Built-in defaults

## IpHub Mirrors

For regions with GitHub access issues:

```yaml
hub:
  url: https://twisker.coding.net/twisker/iphub/raw/main
```

Or via CLI:

```bash
ipman hub search scraper --hub-url https://twisker.coding.net/twisker/iphub/raw/main
```

Or via environment variable:

```bash
export IPMAN_HUB_URL=https://twisker.coding.net/twisker/iphub/raw/main
ipman install web-scraper
```
