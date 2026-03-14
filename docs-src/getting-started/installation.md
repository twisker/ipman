# Installation

## Requirements

- Python 3.10 or later
- One or more supported AI agent tools (Claude Code, OpenClaw)

## Install via PyPI

```bash
pip install ipman-cli
```

## Install via uv

```bash
uv pip install ipman-cli
```

## Install via curl (Linux / macOS)

```bash
curl -sSL https://raw.githubusercontent.com/twisker/ipman/main/install.sh | bash
```

## Verify Installation

```bash
ipman --version
ipman info
```

## Shell Completion

IpMan uses Click, which supports shell completion:

```bash
# Bash
eval "$(_IPMAN_COMPLETE=bash_source ipman)"

# Zsh
eval "$(_IPMAN_COMPLETE=zsh_source ipman)"

# Fish
_IPMAN_COMPLETE=fish_source ipman | source
```
