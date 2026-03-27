# Installation

## Requirements

- **Python**: >= 3.10 (3.12+ recommended)
- **OS**: Linux / macOS / Windows
- One or more supported AI agent tools (Claude Code, OpenClaw)

## Quick Install

### Via pipx (Recommended)

```bash
# macOS
brew install pipx
pipx ensurepath
pipx install ipman-cli

# Linux / Windows
pip install pipx
pipx install ipman-cli
```

> **VPN / Corporate network users**: If you encounter SSL certificate errors, use:
> ```bash
> pipx install ipman-cli --pip-args="--trusted-host pypi.org --trusted-host files.pythonhosted.org"
> ```
> See [FAQ - SSL errors](../faq.md#q-pip-install-fails-with-ssl-certificate_verify_failed) for details.

### Via pip

```bash
pip install ipman-cli
```

> **Note**: Python 3.12+ Homebrew environments block global installs due to [PEP 668](https://peps.python.org/pep-0668/). Use pipx or a virtual environment instead.

### Via uv

```bash
uv pip install ipman-cli
```

### Via curl (Linux / macOS)

```bash
curl -sSL https://raw.githubusercontent.com/twisker/ipman/main/install.sh | bash
```

### Download Pre-built Binary (Windows / macOS / Linux)

Download the latest binary from [GitHub Releases](https://github.com/twisker/ipman/releases):

- `ipman-windows-x64.exe` — Windows
- `ipman-macos-arm64` — macOS (Apple Silicon)
- `ipman-linux-x64` — Linux

Place the binary in your PATH and run `ipman --version` to verify.

## macOS Detailed Steps

If your macOS ships with Python < 3.10 (e.g. 3.9), install a newer version first.

### 1. Install Python 3.12

```bash
brew install python@3.12
```

### 2. Set Python 3.12 as Default

```bash
echo 'export PATH="$(brew --prefix python@3.12)/libexec/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

Verify:

```bash
python3 --version   # Should show 3.12.x
which python3       # Should point to Homebrew path
```

> **Note**: Do not delete or overwrite `/usr/bin/python3` — macOS system tools depend on it. The PATH trick safely shadows the system version.

### 3. Install pipx and IpMan

```bash
brew install pipx
pipx ensurepath
pipx install ipman-cli
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

## Install from Source (Developers)

```bash
git clone https://github.com/twisker/ipman.git
cd ipman
uv venv
uv pip install -e ".[dev]"
```
