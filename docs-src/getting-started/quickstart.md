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
```

## 4. List Installed Skills

```bash
ipman skill list
```

## 5. Pack Your Environment

```bash
ipman pack --name my-kit --version 1.0.0
```

This creates `my-kit.ip.yaml` — a portable skill bundle anyone can install.

## 6. Share via IpHub

```bash
ipman hub publish my-kit.ip.yaml
```

## 7. Deactivate

```bash
ipman env deactivate
```
