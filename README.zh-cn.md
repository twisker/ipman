<p align="center">
  <img src="images/IpMan.jpg" alt="IpMan Banner" width="600" />
</p>

# IpMan - 智能包管理器

*我要打十个。*

> Agent 技能虚拟环境管理器 — 类似 conda/uv，但用于 AI Agent 技能。内置恶意技能防御。

**[English README](README.md)** | **[文档站](https://twisker.github.io/ipman/zh/)** | **[English Docs](https://twisker.github.io/ipman)**

---

[36% 的 AI Agent 技能包含 prompt 注入，824+ 个已确认恶意技能。](https://snyk.io/blog/toxicskills-malicious-ai-agent-skills-clawhub/) IpMan 不仅管理技能，更保护你的安全。

## 为什么选择 IpMan？

AI Agent 技能生态是新的软件供应链 — 但它正在遭受攻击。技能以 **Agent 完整权限** 运行，**默认无沙箱**，发布门槛仅需一个 Markdown 文件，这很危险。
为此，IpMan 为你提供：

- **安装前风险评估** — 每个技能自动扫描凭证窃取、数据外泄、混淆代码、prompt 注入等高危风险
- **四级安全模式** — 从 PERMISSIVE（全部安装）到 STRICT（仅安装安全技能）
- **社区驱动的威胁举报** — 标记可疑技能，举报次数纳入风险评分
- **发布时风控** — HIGH/EXTREME 风险技能在发布环节即被阻止

## 功能特性

### 安全优先

- **风险评估引擎** — 检测凭证收割、混淆代码（base64/eval/exec）、未授权网络调用、提权请求、敏感路径访问（~/.ssh、~/.aws）、prompt 注入模式。风险级别：LOW / MEDIUM / HIGH / EXTREME
- **安全模式** — PERMISSIVE、DEFAULT、CAUTIOUS、STRICT，按需控制风险容忍度
- **智能信任模型** — IpHub 技能携带预评估标注；本地/URL 安装强制触发设备端评估。用 `--vet` 或 `--no-vet` 覆盖
- **安全日志** — 所有阻止/告警的安装记录在 `~/.ipman/security.log`
- **社区举报** — `ipman hub report <name>` 标记可疑技能，举报次数公开展示

### 包管理

- **虚拟环境** — 按项目、用户或机器创建隔离的技能环境
- **IP 包** — 将技能集打包为可分发的 `.ip.yaml` 文件
- **依赖解析** — 递归依赖 + 版本约束（`>=`、`^`、`~`）
- **跨 Agent** — 通过适配器插件支持 Claude Code、OpenClaw 等

### IpHub 注册表

- **搜索浏览** — 按关键词搜索，按 Agent 过滤
- **发布** — 通过自动化 GitHub PR 工作流提交技能/IP 包
- **排名** — 按安装量展示热门技能
- **镜像支持** — 可配置替代 Hub URL，应对区域访问限制（CNB 镜像可用）

## 安装

```bash
# 通过 PyPI
pip install ipman-cli

# 通过 uv
uv pip install ipman-cli

# 通过 curl（Linux / macOS）
curl -sSL https://raw.githubusercontent.com/twisker/ipman/main/install.sh | bash
```

Windows/macOS/Linux 预编译二进制文件可在 [GitHub Releases](https://github.com/twisker/ipman/releases) 下载。

## 快速上手

```bash
# 创建并激活技能环境
ipman env create myenv
ipman env activate myenv

# 安装技能（自动风险评估）
ipman install web-scraper

# 从本地 IP 包安装（强制风险扫描）
ipman install frontend-kit.ip.yaml

# 打包当前环境
ipman pack --name my-kit --version 1.0.0

# 搜索并发布到 IpHub
ipman hub search scraper
ipman hub publish my-skill --description "我的技能"

# 举报可疑技能
ipman hub report sketchy-tool --reason "向未知服务器发送数据"
```

完整指南请查看 **[文档站](https://twisker.github.io/ipman/zh/)**。

## 安全模式

| 模式 | 行为 | 适用场景 |
|------|------|---------|
| `permissive` | 全部安装，仅 EXTREME 告警 | 可信内部环境 |
| `default` | 阻止 EXTREME，HIGH 告警 | 日常使用 |
| `cautious` | 阻止 HIGH+EXTREME，MEDIUM 告警 | 生产环境 |
| `strict` | 仅允许 LOW；所有来源强制本地重新评估 | 高安全部署 |

详见 **[安全指南](https://twisker.github.io/ipman/zh/guide/security/)**。

## IpHub 排名

<!-- TOP_SKILLS_START -->
*有安装数据后，排名将在此显示。*
<!-- TOP_SKILLS_END -->

<!-- TOP_PACKAGES_START -->
<!-- TOP_PACKAGES_END -->

## Star 趋势

[![Star History Chart](https://api.star-history.com/svg?repos=twisker/ipman&type=Date)](https://star-history.com/#twisker/ipman&Date)

## 许可证

Apache License 2.0 — 详见 [LICENSE](LICENSE)。
