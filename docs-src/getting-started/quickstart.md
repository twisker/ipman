# Quick Start

## 1. Create an Environment

```bash
ipman env create myenv
```

This creates an isolated skill environment in your project directory.

## 2. Activate It

```bash
ipman env activate myenv
```

Your shell prompt changes to `[ip:myenv]` to indicate the active environment.

## 3. Install Skills

```bash
# From IpHub (risk-assessed)
ipman install web-scraper

# From a local IP package (auto-scanned for risks)
ipman install frontend-kit.ip.yaml

# Force local risk assessment on IpHub skill
ipman install suspicious-tool --vet

# Install in strict security mode
ipman install some-skill --security strict
```

## 4. List Installed Skills

```bash
ipman skill list
```

## 5. Pack Your Environment

```bash
ipman pack --name my-kit --version 1.0.0
```

This creates `my-kit.ip.yaml` — a portable skill bundle (with version snapshots) anyone can install.

## 6. Share via IpHub

```bash
ipman hub publish my-kit.ip.yaml
```

## 7. Report Suspicious Skills

```bash
ipman hub report sketchy-tool --reason "Sends data to unknown server"
```

## 8. Deactivate

```bash
ipman env deactivate
```
