# Installation

## Requirements

- Python 3.10 or later
- One or more supported AI agent tools (Claude Code, OpenClaw)

## Install via PyPI

```bash
pip install ipman
```

## Install via uv

```bash
uv pip install ipman
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
