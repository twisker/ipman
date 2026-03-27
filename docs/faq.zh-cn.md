# IpMan 常见问题 (FAQ)

## 安装相关

### Q: `pip install ipman-cli` 报错 "no matching distribution found"，怎么办？

此错误有两种常见原因：

**原因 1（最常见）：Python 版本低于 3.10**

IpMan 要求 Python >= 3.10。当你的 Python 版本不满足要求时，PyPI 找不到兼容的发行版。

**原因 2：VPN / 代理导致 SSL 连接失败**

如果你处于 VPN 或企业网络环境，pip 可能因 SSL 证书验证失败而无法连接 PyPI，错误信息有时也会表现为 "no matching distribution"（伴随 SSL 相关警告）。参见下方 [SSL 报错](#q-pip-install-报错-ssl-certificate_verify_failed怎么办) 条目。

**排查步骤**：

```bash
# 1. 确认 Python 版本（必须 >= 3.10）
python3 --version

# 2. 如果版本满足要求，测试 PyPI 连通性
pip index versions ipman-cli
```

**解决**：
- 如果是版本问题，升级 Python 到 3.10+
- 如果是网络问题，参见下方 [SSL 报错](#q-pip-install-报错-ssl-certificate_verify_failed怎么办)

macOS 用户推荐通过 Homebrew 安装：

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

> **VPN 用户注意**：如果 pipx 安装时也报 SSL 错误，需要加信任参数：
> ```bash
> pipx install ipman-cli --pip-args="--trusted-host pypi.org --trusted-host files.pythonhosted.org"
> ```
> 详见下方 [SSL 报错](#q-pip-install-报错-ssl-certificate_verify_failed怎么办) 条目。

**备选方案**：手动创建虚拟环境：

```bash
python3 -m venv ~/.ipman-venv
source ~/.ipman-venv/bin/activate
pip install ipman-cli
```

> **不推荐**：`pip install --break-system-packages ipman-cli` 虽然可以绕过限制，但可能导致 Homebrew 管理的 Python 包损坏。

---

### Q: `pip install` 报错 "SSL: CERTIFICATE_VERIFY_FAILED"，怎么办？

**典型报错**：

```
WARNING: Retrying ... after connection broken by 'SSLError(SSLCertVerificationError(1,
'[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate'))'
```

**原因**：通常是 VPN、企业代理或缺少 CA 根证书导致 pip 无法验证 PyPI 的 SSL 证书。

**方案 1：VPN / 企业代理环境（最常见）**

临时跳过 SSL 验证完成安装：

```bash
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org ipman-cli
```

pipx 用户：

```bash
pipx install ipman-cli --pip-args="--trusted-host pypi.org --trusted-host files.pythonhosted.org"
```

> **提示**：如需永久生效，可写入 pip 配置文件 `~/.pip/pip.conf`：
> ```ini
> [global]
> trusted-host =
>     pypi.org
>     files.pythonhosted.org
> ```

**方案 2：macOS 缺少 CA 证书**

```bash
brew install ca-certificates
```

**方案 3：将企业根证书加入信任链**

如果你的公司网络使用 SSL 中间人代理，需要把公司根证书导入系统钥匙串或 Python 的证书库：

```bash
# 获取公司根证书（通常由 IT 部门提供），然后：
# macOS：双击 .crt 文件导入钥匙串，并设为"始终信任"
# 或：通过环境变量指定
export SSL_CERT_FILE=/path/to/company-root-ca.crt
```

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
