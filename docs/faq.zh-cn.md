# IpMan 常见问题 (FAQ)

## 安装相关

### Q: `pip install ipman-cli` 报错 "no matching distribution found"，怎么办？

**原因**：IpMan 要求 Python >= 3.10。当你的 Python 版本低于 3.10 时，PyPI 找不到兼容的发行版，就会报此错误。

**排查**：先确认当前 Python 版本：

```bash
python3 --version
```

**解决**：升级 Python 到 3.10 或更高版本。macOS 用户推荐通过 Homebrew 安装：

```bash
brew install python@3.12
```

安装后需将其设为默认版本，参见[安装指南](installation-guide.zh-cn.md#2-将-python-312-设为默认版本)。

---

### Q: macOS 上如何将 Homebrew 安装的 Python 3.12 设为默认？

在 `~/.zshrc` 中添加 PATH 配置：

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

---

### Q: Python 3.12 下 `pip install` 报错 "externally-managed-environment"，怎么办？

**原因**：Python 3.12 实施了 [PEP 668](https://peps.python.org/pep-0668/)，禁止 pip 直接向 Homebrew 等包管理器维护的 Python 环境中安装包，以防止系统包管理器和 pip 之间的冲突。

**推荐方案**：使用 pipx 安装 CLI 工具：

```bash
brew install pipx
pipx ensurepath
pipx install ipman-cli
```

pipx 会自动为 ipman-cli 创建独立的虚拟环境，不影响系统 Python 环境。

**备选方案**：手动创建虚拟环境：

```bash
python3 -m venv ~/.ipman-venv
source ~/.ipman-venv/bin/activate
pip install ipman-cli
```

> **不推荐**：`pip install --break-system-packages ipman-cli` 虽然可以绕过限制，但可能导致 Homebrew 管理的 Python 包损坏。

---

### Q: 支持哪些 Python 版本？

IpMan 要求 **Python >= 3.10**。推荐使用 Python 3.12 或更高版本。

不支持 Python 3.9 及以下版本，因为项目使用了 3.10+ 的语言特性（如 `match/case` 模式匹配、`X | Y` 类型联合语法等）。

---

### Q: 支持哪些操作系统？

IpMan 支持 **Linux**、**macOS** 和 **Windows** 三大平台。

---

## 使用相关

### Q: IpMan 支持哪些 Agent 工具？

目前支持：

- **Claude Code**
- **OpenClaw**

IpMan 不侵入 Agent 内部实现，通过标准 CLI 命令与 Agent 交互。

### Q: 如何查看已安装的版本？

```bash
ipman --version
```
