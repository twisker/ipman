# IpHub

IpHub is a community registry for sharing skills and IP packages. It uses GitHub as infrastructure — no separate server needed.

## Search

```bash
ipman hub search scraper
ipman hub search --agent openclaw
```

## Info

```bash
ipman hub info web-scraper
```

## Rankings

```bash
ipman hub top
ipman hub top -n 20
```

## Publish

```bash
# Publish a skill
ipman hub publish web-scraper --description "Browser automation"

# Publish an IP package
ipman hub publish my-kit.ip.yaml
```

Publishing creates a PR to the [iphub](https://github.com/twisker/iphub) repository via `gh` CLI.

## Report Suspicious Skills

```bash
ipman hub report sketchy-tool --reason "Sends data to unknown server"
```

Report counts are publicly visible in `ipman hub info` output.
