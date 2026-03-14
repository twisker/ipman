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

## Download Pre-built Binary (Windows / macOS / Linux)

Download the latest binary from [GitHub Releases](https://github.com/twisker/ipman/releases):

- `ipman-windows-x64.exe` — Windows
- `ipman-macos-arm64` — macOS (Apple Silicon)
- `ipman-linux-x64` — Linux

Place the binary in your PATH and run `ipman --version` to verify.

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
