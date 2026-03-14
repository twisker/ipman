<p align="center">
  <img src="../images/IpMan.jpg" alt="IpMan Banner" width="600" />
</p>

# IpMan - 智能包管理器

*我要打十个。*

> Agent 技能虚拟环境管理器 — 类似 conda/uv，但用于 AI Agent 技能。内置恶意技能防御。

## 什么是 IpMan？

IpMan 管理 AI Agent 技能的方式，就像 conda/uv 管理 Python 包一样 — 隔离环境、依赖解析、社区注册表。但与传统包管理器不同，IpMan 内置**安全优先的风险评估引擎**，保护你免受恶意 Agent 技能的威胁。

## 核心能力

- **虚拟环境** — 按项目、用户或机器隔离技能集
- **风险评估** — 每个技能在安装前扫描凭证窃取、数据外泄、混淆代码
- **安全模式** — 从 PERMISSIVE 到 STRICT 四个级别
- **IP 包** — 将技能集打包为可分发的 `.ip.yaml` 文件
- **IpHub** — 社区注册表，支持搜索、发布和威胁举报
- **跨 Agent** — 通过适配器插件支持 Claude Code、OpenClaw 等

## 快速链接

- [安装指南](getting-started/installation.md)
- [快速上手](getting-started/quickstart.md)
- [安全指南](guide/security.md)
