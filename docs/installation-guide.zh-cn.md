# IpMan 安装指南

## 系统要求

- **Python**: >= 3.10
- **操作系统**: Linux / macOS / Windows
- **推荐安装方式**: pipx（CLI 工具隔离安装）

## 快速安装

### Linux / macOS

```bash
# 推荐：使用 pipx（自动创建隔离环境）
pipx install ipman-cli

# 或：使用 pip（需在虚拟环境中）
python3 -m venv ~/.ipman-venv
source ~/.ipman-venv/bin/activate
pip install ipman-cli
```

### Windows

```powershell
# 推荐：使用 pipx
pipx install ipman-cli

# 或：使用 pip（需在虚拟环境中）
python -m venv %USERPROFILE%\.ipman-venv
%USERPROFILE%\.ipman-venv\Scripts\activate
pip install ipman-cli
```

### 验证安装

```bash
ipman --version
```

## macOS 详细步骤

macOS 用户如果系统自带的 Python 版本低于 3.10，需要先安装新版 Python。

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
python3 --version
# 应显示 Python 3.12.x
```

### 3. 安装 pipx 并安装 IpMan

```bash
brew install pipx
pipx ensurepath
pipx install ipman-cli
```

> **为什么用 pipx 而不是 pip？**
> Python 3.12 引入了 PEP 668 保护机制，Homebrew 管理的 Python 环境会阻止 `pip install` 全局安装包。pipx 专为 CLI 工具设计，自动为每个包创建隔离的虚拟环境，既安全又方便。

> **VPN / 企业网络用户**：如果遇到 SSL 证书验证失败，使用以下命令：
> ```bash
> pipx install ipman-cli --pip-args="--trusted-host pypi.org --trusted-host files.pythonhosted.org"
> ```
> 详见 [FAQ - SSL 报错](faq.zh-cn.md#q-pip-install-报错-ssl-certificate_verify_failed怎么办)。

## 从源码安装（开发者）

```bash
git clone https://github.com/pinkchampagne17/ipman.git
cd ipman
uv venv
uv pip install -e ".[dev]"
```
