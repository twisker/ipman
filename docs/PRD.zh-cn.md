# IpMan 软件需求文档

## 1. 引言

### 1.1 背景
随着 OpenClaw、Claude Code 等 Agent 工具的普及，为其编写技能（skills）已成为一种趋势。然而，由于大量同名技能的存在，用户在寻找、安装和管理不同版本的技能时面临混乱，类似于早期 Python 环境管理的困境。为解决这一问题，需要一款针对技能的虚拟环境管理工具，实现对技能环境的隔离、依赖管理和分发。

### 1.2 目标
开发一款名为 **IpMan (intelligence package manager)** 的命令行工具，实现以下核心目标：
- 提供技能的虚拟环境管理（类比 Python 的 virtualenv/conda/uv）。
- 适用于主流 Agent 工具（至少包括 OpenClaw、Claude Code）。
- 跨平台支持（Linux、macOS、Windows）。
- 支持将一组技能打包为基于文本文件的 **Intelligence Package (IP)**，便于安装和分发。
- 提供IpHub（类比 PyPI）。
- 保持与 Agent 工具内部结构的解耦，通过标准命令进行技能管理。

## 2. 总体描述

### 2.1 产品范围
IpMan 是一个纯命令行工具，专注于 Agent 技能的环境管理。它允许用户创建、切换、删除虚拟环境，安装、卸载、发布技能和 IP 包，并与IpHub交互。IpMan 不修改 Agent 工具的内部实现，仅通过调用 Agent 的标准技能管理接口或操作技能存放目录（通过软链接等方式）来实现隔离。

### 2.2 用户特征
- **技能开发者**：需要为不同项目隔离技能环境，避免版本冲突；希望发布自己的技能或 IP 包到 IpHub。
- **技能使用者**：希望快速安装、试用不同技能，并在项目间切换环境；需要清晰了解技能的详细信息（功能、作者、版本等）以避免混淆。
- **项目维护者**：需要为项目定义一组固定的技能依赖，便于团队协作和部署。

### 2.3 假设与依赖
- 用户已安装一种或多种受支持的 Agent 工具（OpenClaw、Claude Code 等）。
- IpHub利用 GitHub 等免费基础设施实现数据存储（如使用 GitHub Issues、GitHub Pages 或 GitHub Actions 进行简单计数和元数据存储）；若不可行，则使用低成本 OSS 方案。
- 用户系统具备 Python 运行环境（IpMan 本身以 Python 编写）。
- 网络连接用于访问IpHub。

## 3. 功能需求

### 3.1 虚拟环境管理
| 需求ID | 描述 | 来源 |
|--------|------|------|
| FR1 | 提供虚拟环境的创建、激活、停用、删除、列表查看功能。 | 主要目标1 |
| FR2 | 虚拟环境的实现应基于软链接（symbolic link）将实际技能存储位置与项目环境分离（类似 nvm 对 npm 的管理方式），便于切换和隔离。 | 细节要求1 |
| FR3 | 支持针对不同作用域（scope）创建虚拟环境：<br>- `--project`：在当前项目目录下创建环境（缺省）。<br>- `--user`：为当前用户创建环境。<br>- `--machine`：为整个机器创建环境。 | 细节要求28 |
| FR4 | 环境激活后，系统命令行提示符应醒目地改变，以提醒用户当前处于 IpMan 管理的虚拟环境中。提示符格式需与 Python 虚拟环境（如 virtualenv）有明显区分。 | 细节要求31 |

### 3.2 技能管理
| 需求ID | 描述 | 来源 |
|--------|------|------|
| FR5 | 支持在虚拟环境中安装、卸载、升级、列出技能。技能管理方式应借鉴 `uv` 的模式（如快速依赖解析、锁定文件等）。 | 主要目标2，细节要求2 |
| FR6 | 技能安装时需记录详细的元数据：功能简介、详细介绍、来源 URL、版本、作者、依赖关系等，以解决同名技能混淆问题。 | 细节要求5，17 |
| FR7 | 支持在虚拟环境中安装单独发布的技能（即不打包为 IP），且技能发布时需包含元数据（功能简介、短名称、版本、依赖性等）。 | 细节要求17 |
| FR8 | 支持从本地 IP 文件离线安装技能或 IP 包。 | 细节要求7 |
| FR9 | 支持从IpHub按简单名称安装技能或 IP 包（参考 pip 的 `install <package>`）。 | 细节要求8 |
| FR10 | 支持技能依赖的自动解析和安装（包括递归安装 IP 包的依赖）。 | 细节要求21 |

### 3.3 IP 包管理
| 需求ID | 描述 | 来源 |
|--------|------|------|
| FR11 | 支持将一组技能打包为一个 IP 包，IP 包定义基于文本文件（格式待定，如 JSON/YAML/TXT，需斟酌）。 | 主要目标4，细节要求3 |
| FR12 | IP 文本文件应包含：<br>- 包的基本信息：名称、版本、简要说明、详细介绍、作者信息。<br>- 引用的技能列表：每个技能需包含功能介绍、来源 URL、版本、作者等信息。<br>- 依赖的其他 IP 包（支持递归引用）。<br>- 支持注释。 | 细节要求4，5，20，24 |
| FR13 | IpMan 自动生成的 IP 文件，其头部注释应包含指向 IpMan 项目代码库的引用及简单安装说明，方便任何拿到 IP 文件的人了解如何安装。 | 细节要求25 |
| FR14 | 支持将当前虚拟环境中的技能导出为 IP 文件。 | 隐含 |
| FR15 | 支持从 IP 文件安装所有技能到当前虚拟环境，并自动处理依赖。 | 细节要求7，21 |

### 3.4 IpHub 交互
| 需求ID | 描述 | 来源 |
|--------|------|------|
| FR16 | 提供一个IpHub，支持用户搜索、浏览、下载技能和 IP 包。 | 主要目标5 |
| FR17 | IpHub 应记录每个技能和 IP 包的安装/下载次数，并支持排名（Top 10/20/50）。 | 细节要求6，20 |
| FR18 | 支持将本地的技能或 IP 包发布到 IpHub（需用户认证，认证方式待定）。 | 细节要求8 |
| FR19 | IpHub 的持久化数据应优先利用 GitHub 免费资源实现（如 Issues、Pages、Actions 等）；若不可行，则使用公共免费基础设施；最后考虑低成本 OSS。 | 细节要求9 |
| FR20 | 项目主页（README）应动态展示 Top 10 技能和 Top 10 IP 包的排名。 | 细节要求22 |
| FR21 | 项目主页还应展示自身项目的 GitHub Star 趋势图。 | 细节要求23 |

### 3.5 项目集成与工具探测
| 需求ID | 描述 | 来源 |
|--------|------|------|
| FR22 | IpMan 应能探测本机已安装的受支持 Agent 工具（如 OpenClaw、Claude Code）及其版本。 | 细节要求29 |
| FR23 | 在当前项目目录运行时，IpMan 应根据项目文件和目录结构自动猜测项目所使用的 Agent 工具，并针对该工具创建技能环境。 | 细节要求26 |
| FR24 | 允许用户通过参数（`--agent`）显式指定目标 Agent 工具，覆盖自动探测结果。 | 细节要求26 |
| FR25 | 当创建虚拟环境时，如果当前项目已安装部分技能（例如在全局作用域），应提供参数（`--inherit`）让用户选择是否继承这些已安装的技能到新环境。 | 细节要求27 |

### 3.6 命令行界面
| 需求ID | 描述 | 来源 |
|--------|------|------|
| FR26 | 所有命令、参数、说明文字默认以英文提供；若检测到系统环境支持中文（如 `LANG` 环境变量含 `zh`），则说明性文字和提示性文字自动切换为中文。 | 细节要求10 |
| FR27 | 提供全面的帮助文档和教程，至少包含英文和中文两个版本。 | 细节要求11 |
| FR28 | 文档中需包含 IP 文本文件格式的 schema（格式标准说明）。 | 细节要求30 |

## 4. 非功能需求

### 4.1 平台兼容性
| 需求ID | 描述 | 来源 |
|--------|------|------|
| NFR1 | 工具必须支持 Linux、macOS、Windows 三大主流操作系统。 | 主要目标3 |
| NFR2 | 在 Windows 平台上需提供预编译的可执行文件及安装包，并支持 CI/CD 自动编译打包。 | 细节要求14，19 |

### 4.2 可用性
| 需求ID | 描述 | 来源 |
|--------|------|------|
| NFR3 | 工具应保持与 Agent 内部结构的解耦，所有技能安装、卸载等操作均通过调用 Agent 提供的标准接口或通过软链接实现，避免直接侵入 Agent 特有目录结构。 | 主要目标6 |
| NFR4 | 环境切换应快速、可靠，不干扰同一机器上其他项目或 Agent 的正常使用。 | 隐含 |

### 4.3 文档与国际化
| 需求ID | 描述 | 来源 |
|--------|------|------|
| NFR5 | 提供英文和中文两套完整的帮助文档、教程，且需通过 CI/CD 流程自动生成（如从 Markdown 源文件构建为 HTML/PDF 等）。 | 细节要求11，15 |
| NFR6 | 文档需包含 IP 文件格式的详细 schema 说明。 | 细节要求30 |

### 4.4 发布与安装
| 需求ID | 描述 | 来源 |
|--------|------|------|
| NFR7 | IpMan 本身支持多种安装方式：<br>- 通过 PyPI 安装（`pip install ipman`）。<br>- 通过 curl+shell 脚本安装（适用于 Unix-like 系统）。<br>- Windows 安装包（如 .exe 或 .msi）。 | 细节要求13 |
| NFR8 | 每个版本发布时，应提供源码 tar 包以及 Windows 预编译版本和安装包。 | 细节要求14 |
| NFR9 | 所有发布资源应通过 CI/CD 自动化流程生成和发布。 | 细节要求14 |
| NFR10 | 版本发布时，CI/CD 流程应自动将 IpMan 包发布到 PyPI。 | 新增 |

### 4.5 开发与测试
| 需求ID | 描述 | 来源 |
|--------|------|------|
| NFR11 | 开发过程遵循 TDD（测试驱动开发），每个版本发布前必须在三个目标平台（Linux、macOS、Windows）上通过所有测试用例。 | 细节要求18 |
| NFR12 | 需搭建自动化测试框架，能在三个平台上自动运行测试用例。 | 细节要求18 |
| NFR13 | 项目托管在 GitHub 上，并利用 GitHub Actions 等实现 CI/CD。 | 细节要求16 |
| NFR14 | 项目代码库遵循 Git Flow 分支规则，并在 release 分支合并到 main 分支时触发版本发布流程。 | 新增 |

### 4.6 数据存储与统计
| 需求ID | 描述 | 来源 |
|--------|------|------|
| NFR15 | IpHub的安装/下载量统计数据应准确记录，并用于排名展示。 | 细节要求6，20 |
| NFR16 | 数据存储优先使用 GitHub 免费资源（如通过 GitHub Issues 计数、GitHub Pages 展示静态数据），并考虑数据持久性。 | 细节要求9 |

## 5. 外部接口需求

### 5.1 用户界面
- **命令行接口**：所有功能通过命令行调用，符合常见 CLI 习惯（如 `ipman create`, `ipman activate`, `ipman install` 等）。支持 `--help` 查看帮助。

### 5.2 与 Agent 工具的接口
- **技能安装/卸载**：IpMan 需调用 Agent 工具提供的标准技能管理命令，或通过操作技能存放目录的软链接来实现。具体实现方式需针对不同 Agent 进行适配，但保持内部逻辑解耦。

### 5.3 与IpHub的接口
- **HTTP/HTTPS 通信**：用于从 IpHub 下载技能元数据和包内容、上传发布包、获取统计数据等。IpHub 可能提供 RESTful API。

## 6. 约束

- **开发语言**：IpMan 必须以 Python 语言实现。
- **开源托管**：项目必须托管在 GitHub 上，并采用合适的开源许可证（如 MIT、Apache 2.0 等）。
- **版本管理**：遵循语义化版本规范（SemVer）。
- **分支管理**：项目代码库遵循 Git Flow 分支规则，在 release 分支合并到 main 分支时触发版本发布流程。（已包含在 NFR14）
- **依赖管理**：应尽量减少外部依赖，或确保依赖跨平台兼容。

---

## 附录 A：IP 文本文件格式草案（待定）
- 可选格式：JSON、YAML 或自定义 TXT。需支持注释。
- 基本结构示例（以 YAML 为例）：
  ```yaml
  # IpMan package file - see https://github.com/twisker/ipman for installation
  name: my-skillset
  version: 1.0.0
  description: A collection of useful skills for web research
  author:
    name: John Doe
    email: john@example.com
  skills:
    - name: web-scraper
      version: 2.1.0
      source: https://github.com/agent-skills/web-scraper
      description: Extracts data from websites
      author: Agent Skills Team
    - name: summarizer
      version: 1.3.2
      source: https://github.com/other/summarizer
      description: Summarizes text using NLP
  dependencies:
    - base-utils@^1.0.0
  ```
- 具体 schema 将在后续文档中详细定义。

---

## 7. 安全需求 (v2.0)

> 2026-03-14 新增。应对 AI Agent 技能生态日益严峻的安全威胁。
> 参考：[Skill Vetter](https://clawhub.ai/spclaudehome/skill-vetter)、[Snyk ToxicSkills](https://snyk.io/blog/toxicskills-malicious-ai-agent-skills-clawhub/)

### 7.1 威胁背景

AI Agent 技能生态面临严重安全威胁：
- ClawHub 上 36% 的 skill 包含 prompt 注入（Snyk ToxicSkills 研究，2026年2月）
- 13.4% 存在关键安全问题；824+ 个已确认的恶意 skill
- 攻击手法包括：凭证窃取、数据外泄、混淆代码执行、prompt 注入
- 技能以 Agent 完整权限运行，默认无沙箱隔离

### 7.2 技能风险评估引擎

| 需求ID | 描述 |
|--------|------|
| FR-S1 | IpMan 须内置风险评估引擎，在安装前分析 skill 和 IP 包的安全风险。引擎设计参考 [Skill Vetter](https://clawhub.ai/spclaudehome/skill-vetter)，或在可行时直接调用。 |
| FR-S1.1 | 风险分级：🟢 LOW（无问题）、🟡 MEDIUM（存在关注点）、🔴 HIGH（存在红旗）、⛔ EXTREME（可能恶意）。 |
| FR-S1.2 | 红旗检测：向未知 URL 发起 curl/wget、凭证收割（API key、token、~/.ssh、~/.aws 等）、混淆代码（base64、压缩、eval/exec）、sudo/root 请求、向原始 IP 地址发起网络调用、访问 Agent 记忆文件。 |
| FR-S1.3 | 权限范围分析：文件读写范围、网络调用目标、命令执行、范围最小化检查（最小权限原则）。 |
| FR-S1.4 | 来源信誉检查：作者历史记录、下载量、仓库年龄/星标数、社区评价。 |
| FR-S1.5 | 输出：结构化风险报告，包含风险级别、检测到的标志、权限摘要和安装建议（安全安装 / 谨慎安装 / 不建议安装）。 |

### 7.3 IpHub 举报与标记系统

| 需求ID | 描述 |
|--------|------|
| FR-S2 | IpHub 须支持社区驱动的举报机制，用于标记可疑 skill/IP 包。 |
| FR-S2.1 | 举报提交命令：`ipman hub report <name> --reason <描述>`。 |
| FR-S2.2 | 举报次数作为元数据记录在 IpHub 注册表中，在 `ipman hub info` 输出中醒目展示。 |
| FR-S2.3 | 收到举报后，系统重新运行风险评估并更新风险标签。 |
| FR-S2.4 | 高举报次数作为输入信号，纳入风险级别评估的参考依据。 |

### 7.4 发布时风险评估

| 需求ID | 描述 |
|--------|------|
| FR-S3 | 通过 `ipman hub publish` 发布时，在创建 PR 前自动调用风险评估引擎。 |
| FR-S3.1 | 风险级别写入注册文件的元数据。 |
| FR-S3.2 | 若风险级别为 HIGH 或 EXTREME，阻止发布并给出说明。 |
| FR-S3.3 | 风险评估结果包含在 PR 正文中供审阅者参考。 |

### 7.5 安装时安全执行策略

| 需求ID | 描述 |
|--------|------|
| FR-S4 | IpMan 须在安装过程中根据当前安全模式执行安全策略。 |
| FR-S4.1 | **IpHub 来源（默认信任）：** 信任 IpHub 上的现有风险标注；跳过本地评估，除非处于 STRICT 模式或指定了 `--vet` 参数。 |
| FR-S4.2 | **本地文件 / URL / 自定义 hub 来源：** 安装前必须运行本地风险评估，除非指定 `--no-vet` 参数。 |
| FR-S4.3 | 安装时动作矩阵： |

| 风险级别 | PERMISSIVE | DEFAULT | CAUTIOUS | STRICT |
|---------|------------|---------|----------|--------|
| 🟢 LOW | 安装 | 安装 | 安装 | 安装 |
| 🟡 MEDIUM | 安装 | 安装 | 告警+安装 | 告警+确认 |
| 🔴 HIGH | 安装 | 告警+安装 | 阻止 | 阻止 |
| ⛔ EXTREME | 告警+安装 | 阻止 | 阻止 | 阻止 |

| 需求ID | 描述 |
|--------|------|
| FR-S4.4 | **阻止：** 拒绝安装，显示风险报告，写入安全日志文件。 |
| FR-S4.5 | **告警+确认：** 显示告警信息，需要用户明确确认（`--yes` 可跳过确认）。 |

### 7.6 安全模式级别

| 需求ID | 描述 |
|--------|------|
| FR-S5 | IpMan 须支持四个安全模式级别：PERMISSIVE（宽松）、DEFAULT（默认）、CAUTIOUS（谨慎）、STRICT（严格）。 |
| FR-S5.1 | 安全模式优先级：命令行参数 `--security <mode>` > 配置文件 `security.mode` > 内置默认值（DEFAULT）。 |
| FR-S5.2 | 在 STRICT 模式下，所有安装来源均触发本地风险评估，无论 IpHub 上是否已有标注。 |

### 7.7 安全日志

| 需求ID | 描述 |
|--------|------|
| FR-S6 | 当 skill/IP 被阻止或产生告警时，须向安全日志文件写入一条记录。 |
| FR-S6.1 | 日志条目包括：时间戳、skill 名称、来源、风险级别、风险详情、执行动作（阻止/告警/已安装）。 |
| FR-S6.2 | 日志路径可通过配置文件设置；默认：`~/.ipman/security.log`。 |
| FR-S6.3 | 可通过配置禁用日志：`security.log_enabled: false`。 |

### 7.8 配置文件

| 需求ID | 描述 |
|--------|------|
| FR-S7 | IpMan 须支持 `~/.ipman/config.yaml` 配置文件，用于设置参数默认值。 |
| FR-S7.1 | 支持的字段：`security.mode`、`security.log_enabled`、`security.log_path`、`hub.url`、`agent.default`。 |
| FR-S7.2 | 优先级顺序：命令行参数 > 环境变量 > 配置文件 > 内置默认值。 |

示例：
```yaml
# ~/.ipman/config.yaml
security:
  mode: default          # permissive | default | cautious | strict
  log_enabled: true
  log_path: ~/.ipman/security.log

hub:
  url: https://raw.githubusercontent.com/twisker/iphub/main
  # 镜像示例：
  # url: https://cnb.cool/lutuai/twisker/iphub/raw/main

agent:
  default: auto          # auto | claude-code | openclaw
```

### 7.9 IpHub 镜像支持

| 需求ID | 描述 |
|--------|------|
| FR-S8 | IpMan 须支持配置替代 IpHub 注册表 URL，以应对区域访问限制或网络速度限制。 |
| FR-S8.1 | 镜像 URL 可通过以下方式配置：配置文件 `hub.url`、命令行参数 `--hub-url <url>`、环境变量 `IPMAN_HUB_URL`。 |
| FR-S8.2 | 镜像 URL 指向具有相同 index.yaml 和注册文件结构的替代托管。 |

### 7.10 阿里云CNB镜像

| 需求ID | 描述 |
|--------|------|
| FR-S9 | 须在CNB (cnb.cool)上以公开代码库形式维护一个官方 IpHub 镜像。 |
| FR-S9.1 | 主 iphub 仓库上的 GitHub Actions 工作流在每次合并到 main 时自动同步到CNB。 |
| FR-S9.2 | GitHub 访问受限地区的用户可将 `hub.url` 配置为CNB镜像 URL。 |

---

**文档版本**：2.0
**最后更新**：2026-03-14