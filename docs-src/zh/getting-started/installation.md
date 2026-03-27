# 安装

## 环境要求

- **Python**: >= 3.10（推荐 3.12+）
- **操作系统**: Linux / macOS / Windows
- 已安装至少一种支持的 AI Agent 工具（Claude Code、OpenClaw）

## 快速安装

### 通过 pipx 安装（推荐）

```bash
# macOS
brew install pipx
pipx ensurepath
pipx install ipman-cli

# Linux / Windows
pip install pipx
pipx install ipman-cli
```

> **VPN / 企业网络用户**：如果遇到 SSL 证书验证失败，使用以下命令：
> ```bash
> pipx install ipman-cli --pip-args="--trusted-host pypi.org --trusted-host files.pythonhosted.org"
> ```
> 详见 [FAQ - SSL 报错](../faq.md#q-pip-install-报错-ssl-certificate_verify_failed怎么办)。

### 通过 pip 安装

```bash
pip install ipman-cli
```

> **注意**：Python 3.12+ 的 Homebrew 环境会因 [PEP 668](https://peps.python.org/pep-0668/) 阻止全局安装。建议使用 pipx 或虚拟环境。

### 通过 uv 安装

```bash
uv pip install ipman-cli
```

### 通过 curl 安装（Linux / macOS）

```bash
curl -sSL https://raw.githubusercontent.com/twisker/ipman/main/install.sh | bash
```

### 下载预编译二进制文件（Windows / macOS / Linux）

从 [GitHub Releases](https://github.com/twisker/ipman/releases) 下载最新版本：

- `ipman-windows-x64.exe` — Windows
- `ipman-macos-arm64` — macOS (Apple Silicon)
- `ipman-linux-x64` — Linux

将二进制文件放入 PATH 目录即可使用。

## macOS 详细步骤

如果你的 macOS 自带 Python 版本低于 3.10（如 3.9），需要先安装新版 Python。

### 1. 安装 Python 3.12

```bash
brew install python@3.12
```

### 2. 将 Python 3.12 设为默认版本

```bash
echo 'export PATH="$(brew --prefix python@3.12)/libexec/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

验证：

```bash
python3 --version   # 应显示 3.12.x
which python3       # 应指向 Homebrew 路径
```

> **注意**：不要删除或覆盖 `/usr/bin/python3`，macOS 系统工具可能依赖它。上述方法通过 PATH 优先级"遮盖"系统版本，安全且可逆。

### 3. 安装 pipx 并安装 IpMan

```bash
brew install pipx
pipx ensurepath
pipx install ipman-cli
```

## 验证安装

```bash
ipman --version
ipman info
```

## Shell 自动补全

IpMan 基于 Click，支持 Shell 自动补全：

```bash
# Bash
eval "$(_IPMAN_COMPLETE=bash_source ipman)"

# Zsh
eval "$(_IPMAN_COMPLETE=zsh_source ipman)"

# Fish
_IPMAN_COMPLETE=fish_source ipman | source
```

## 从源码安装（开发者）

```bash
git clone https://github.com/twisker/ipman.git
cd ipman
uv venv
uv pip install -e ".[dev]"
```
