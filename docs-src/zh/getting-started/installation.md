# 安装

## 环境要求

- Python 3.10 或更高版本
- 已安装至少一种支持的 AI Agent 工具（Claude Code、OpenClaw）

## 通过 PyPI 安装

```bash
pip install ipman-cli
```

## 通过 uv 安装

```bash
uv pip install ipman-cli
```

## 通过 curl 安装（Linux / macOS）

```bash
curl -sSL https://raw.githubusercontent.com/twisker/ipman/main/install.sh | bash
```

## 下载预编译二进制文件（Windows / macOS / Linux）

从 [GitHub Releases](https://github.com/twisker/ipman/releases) 下载最新版本：

- `ipman-windows-x64.exe` — Windows
- `ipman-macos-arm64` — macOS (Apple Silicon)
- `ipman-linux-x64` — Linux

将二进制文件放入 PATH 目录即可使用。

## 验证安装

```bash
ipman --version
ipman info
```
