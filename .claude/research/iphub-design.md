# IpHub 设计方案

**设计日期：** 2026-03-14
**最后更新：** 2026-03-14（v2 — skill 无版本、IP 分文件、双模式安装）

---

## 一、核心定位

**IpHub = 引用注册表**，不存储任何 skill 内容，只存储对原生 skill 的引用信息。

| 概念 | 类比 |
|------|------|
| IpHub | DNS（名称解析）+ awesome-list（发现） |
| Skill 注册 | "这个 skill 在哪里，怎么用 agent CLI 装" |
| IP 注册 | "这组 skill 该装哪些" |
| ipman install | 解析引用 → 调用 agent CLI → 原生安装 |

**核心原则：**
- IpHub 只存引用，不存 skill 内容，不打包，不代理下载
- 所有安装通过 agent 的原生 CLI 命令完成
- IpMan 是调度者，不是包管理器

---

## 二、仓库结构

IpHub 是一个普通的 GitHub 仓库（`twisker/iphub`）：

```
iphub/
├── index.yaml                      # 全量索引（自动生成，勿手动编辑）
├── registry/
│   ├── @twisker/
│   │   ├── web-scraper.yaml        # Skill 注册（单文件）
│   │   └── frontend-toolkit/       # IP 包注册（目录，分版本文件）
│   │       ├── meta.yaml           # 元信息（作者、描述、许可）
│   │       ├── 1.0.0.yaml          # 版本内容（skills + dependencies）
│   │       └── 2.0.0.yaml
│   └── @alice/
│       └── git-helper.yaml
├── stats/
│   └── downloads.yaml              # 安装统计（自动生成）
├── .github/
│   └── workflows/
│       ├── validate-pr.yaml        # PR 校验（schema + 权限 + 唯一性）
│       ├── post-merge.yaml         # 合并后更新 index + 创建 counter issue
│       └── update-stats.yaml       # 每日统计汇总
└── README.md                       # 自动生成 Top 10
```

---

## 三、注册文件格式

### 3.1 Skill 注册文件（单文件）

Skill 没有语义化版本。Agent CLI 不支持版本指定，安装时永远安装源头最新版。

```yaml
# registry/@twisker/web-scraper.yaml
type: skill
name: web-scraper
description: "Browser automation for web scraping"
author: "@twisker"
license: MIT
homepage: https://github.com/twisker/skill-web-scraper
keywords: [browser, scraping, automation]

agents:
  claude-code:
    plugin: "web-scraper@twisker-plugins"
    marketplace: "https://github.com/twisker/twisker-plugins"
  openclaw:
    slug: "web-scraper"
    hub: "https://clawhub.com"

history:
  - commit: "a1b2c3d"
    date: 2026-03-14
  - commit: "e4f5g6h"
    date: 2026-02-01
```

- `agents` — 安装源信息，不随版本变化
- `history` — 纯记录（commit hash + 登记时间），不参与安装逻辑
- 无 `version` 字段、无 `versions` 数组

### 3.2 IP 包注册文件（分文件存储）

IP 包有真正的版本控制。每个版本一个独立文件，元信息单独存放。

**meta.yaml** — 跨版本共享的元信息：
```yaml
# registry/@twisker/frontend-toolkit/meta.yaml
type: ip
name: frontend-toolkit
description: "Essential skills for frontend development"
author: "@twisker"
license: MIT
homepage: https://github.com/twisker/frontend-toolkit
```

**版本文件** — 特定版本的完整内容：
```yaml
# registry/@twisker/frontend-toolkit/2.0.0.yaml
version: "2.0.0"
released: 2026-03-14

skills:
  - name: css-helper
  - name: react-patterns
  - name: a11y-checker

dependencies:
  - name: base-utils
    version: ">=1.0.0"
```

### 3.3 Agent 安装源配置

| Agent | 字段 | 缺省值 | 说明 |
|-------|------|--------|------|
| Claude Code | `marketplace` | 无（用 agent 已配置的） | Claude plugin marketplace GitHub 仓库 URL |
| OpenClaw | `hub` | `https://clawhub.com` | ClawHub 地址，支持非官方 hub |

---

## 四、索引文件

`index.yaml` 由 GitHub Actions 自动生成，**禁止手动编辑**。

```yaml
# index.yaml（自动生成）
skills:
  web-scraper:
    owner: "@twisker"
    type: skill
    description: "Browser automation for web scraping"
    agents: [claude-code, openclaw]
    counter_issue: 42
    installs: 1234
    unique_users: 567
  git-helper:
    owner: "@alice"
    type: skill
    description: "Git workflow automation"
    agents: [claude-code]
    counter_issue: 43
    installs: 890
    unique_users: 234

packages:
  frontend-toolkit:
    owner: "@twisker"
    type: ip
    latest: "2.0.0"
    versions: ["2.0.0", "1.0.0"]
    description: "Essential skills for frontend development"
    counter_issue: 44
    installs: 456
    unique_users: 123
```

> **注意：** skills 条目无 `latest`/`versions` 字段（skill 没有版本概念）；
> packages 条目有 `latest` + `versions` 列表（IP 包有真正的版本控制）。

### 短名称规则

| 规则 | 说明 |
|------|------|
| 全局唯一 | 不同 namespace 下也不能重名 |
| 先到先得 | 首个注册者拥有该短名称 |
| 不可转让 | 短名称绑定 owner（除非 owner 主动放弃） |
| 命名规范 | 小写字母 + 数字 + 连字符，3-50 字符 |
| Skill 和 IP 共享命名空间 | skill 和 IP 之间也不能重名 |

---

## 五、本地 IP 文件格式（.ip.yaml）

IP 文件是用户本地使用的技能清单文件，可独立于 IpHub 存在。

### 5.1 双模式安装

IP 文件中的 skills 和 dependencies 都支持两种安装模式：

| 有 `source` 字段？ | 模式 | 行为 |
|-------------------|------|------|
| 无 | IpHub 模式 | 查 index.yaml → 读注册文件 → 调 agent CLI |
| 有（skill） | 直接模式 | 从 source 读取 agent 安装源 → 直接调 agent CLI |
| 有（dependency，路径/URL） | 直接模式 | 加载本地文件或下载远程 .ip.yaml → 递归安装 |

安装程序通过**是否存在 `source` 字段**自动区分。

### 5.2 版本语义

| 项 | version 字段 | 可强制执行？ |
|----|-------------|------------|
| IpHub skill | 无此字段（agent CLI 不支持版本指定） | 否 |
| 直接安装源 skill | 无此字段（版本由源头决定） | 否 |
| IpHub IP 包依赖 | 版本约束，匹配 IpHub 可用版本 | 是 |
| 直接路径 IP 包依赖 | 无此字段（文件本身即版本） | 是（隐式） |

### 5.3 版本约束语法（仅用于 IP 包依赖）

| 语法 | 含义 |
|------|------|
| `>=1.2.0` | 大于等于 |
| `^1.3.0` | 兼容更新（>=1.3.0, <2.0.0） |
| `~1.3.0` | 补丁更新（>=1.3.0, <1.4.0） |
| `1.2.0` | 精确版本 |

### 5.4 完整示例

```yaml
# IpMan Intelligence Package — https://github.com/twisker/ipman
# Install: ipman install frontend-kit.ip.yaml

name: frontend-kit
version: "2.0.0"
description: "Frontend development skill collection"
author:
  name: "Twisker"
  github: "@twisker"
license: MIT

skills:
  # IpHub 模式（无 version，装最新）
  - name: css-helper
  - name: a11y-checker

  # 直接安装源模式（指定 agent 安装参数）
  - name: our-design-system
    description: "Internal design system skills"
    source:
      claude-code:
        plugin: "design-system@our-plugins"
        marketplace: "https://github.com/ourorg/claude-plugins"
      openclaw:
        slug: "our-design-system"
        hub: "https://internal-hub.ourorg.com"

dependencies:
  # IpHub IP 包（版本约束有效）
  - name: base-utils
    version: ">=1.0.0"

  # 直接 IP 文件（文件本身即版本）
  - name: team-standards
    source: "https://raw.githubusercontent.com/ourorg/ips/main/standards.ip.yaml"
```

---

## 六、发布流程

### 6.1 发布 Skill

```
ipman hub publish web-scraper

  1. 读取本地 GitHub 身份（gh auth status → @twisker）
  2. 交互式填写/确认注册信息（或读取本地 skill.yaml）
  3. Fork iphub 仓库（若未 fork）
  4. 在 fork 中创建 registry/@twisker/web-scraper.yaml
  5. 向 iphub 主仓库提 PR
     ← PR author = @twisker（GitHub 平台记录，不可伪造）
  6. CI 自动校验 → 自动合并
  7. Post-merge Action：
     - 重新生成 index.yaml
     - 创建 counter issue: "[counter] web-scraper"
```

### 6.2 发布 IP 包

```
ipman hub publish frontend-toolkit.ip.yaml

  1. 读取本地 GitHub 身份
  2. 校验：引用的所有 IpHub skill 在 index.yaml 中存在
  3. Fork iphub 仓库
  4. 创建 registry/@twisker/frontend-toolkit/meta.yaml（首次）
  5. 创建 registry/@twisker/frontend-toolkit/2.0.0.yaml（版本文件）
  6. 提 PR → CI 校验 → 自动合并
  7. Post-merge Action 更新 index + 创建 counter issue
```

---

## 七、安装流程

### 7.1 安装 Skill（IpHub 模式）

```
ipman install web-scraper

  1. 拉取 index.yaml → 查找 web-scraper（type=skill）
  2. 读取 registry/@twisker/web-scraper.yaml
  3. 检测当前 agent（如 claude-code）
  4. 读取 agents.claude-code 配置:
       plugin: "web-scraper@twisker-plugins"
       marketplace: "https://github.com/twisker/twisker-plugins"
  5. 执行 agent CLI 命令:
       claude plugin marketplace add twisker-plugins \
         https://github.com/twisker/twisker-plugins
       claude plugin install web-scraper@twisker-plugins
  6. 安装成功 → 向 counter issue 添加 comment + reaction
```

### 7.2 安装 IP 文件（本地/远程）

```
ipman install frontend-kit.ip.yaml

  1. 检测参数是文件路径 → 加载 .ip.yaml
  2. 解析 dependencies（递归展开，版本匹配）
  3. 汇总所有 skills（去重）
  4. 逐一安装：
     - 有 source → 直接模式（从 source 读 agent 参数 → 调 agent CLI）
     - 无 source → IpHub 模式（查 index → 读注册文件 → 调 agent CLI）
```

### 7.3 安装时的名称解析

```bash
ipman install web-scraper              # 短名称 → 查 index.yaml
ipman install @twisker/web-scraper     # 全名 → 直接定位
ipman install frontend-kit.ip.yaml     # 文件路径 → 本地 IP 安装
ipman install https://.../.ip.yaml     # URL → 下载后安装
```

---

## 八、身份认证与权限

### 认证方式

- 用户身份 = GitHub 账号
- 认证凭证 = 本机 `gh` CLI 的 GitHub token
- PR author = GitHub 平台记录，不可伪造

### CI 权限校验（validate-pr.yaml）

```
PR 触发时：
  pr_author = github.event.pull_request.user.login

  for file in changed_files:
      # 只允许修改自己命名空间下的文件
      if not file.startswith(f"registry/@{pr_author}/"):
          ❌ 拒绝

      # 不允许修改自动生成的文件
      if file in ["index.yaml", "stats/*", "README.md"]:
          ❌ 拒绝

  # 校验 YAML schema
  # 校验短名称全局唯一性
  # 校验引用的 skill 存在（IP 包）
  ✅ 自动合并
```

### 文件权限模型

| 文件 | 谁能改 | 机制 |
|------|--------|------|
| `registry/@twisker/*` | 仅 @twisker | CI 校验 PR author == namespace |
| `index.yaml` | 无人 | post-merge Action 自动生成 |
| `stats/*` | 无人 | 定时 Action 自动生成 |
| `README.md` | 无人 | 定时 Action 自动生成 |
| `.github/workflows/*` | 仅 repo admin | GitHub 分支保护规则 |

---

## 九、安装统计

### 计数机制

每个 skill/IP 在 iphub 仓库有一个对应的 GitHub issue（post-merge 自动创建）。

| 计数方式 | 含义 | GitHub 特性 |
|---------|------|------------|
| Issue comment | 累计安装次数 | 可重复，每次安装一条 |
| Issue reaction (👍) | 独立用户数 | 天然去重，一人一次 |

### 统计汇总（每日定时 Action）

```
1. 遍历所有 [counter] label 的 issues
2. 统计每个 issue 的 comment 数 + reaction 数
3. 写入 stats/downloads.yaml
4. 按安装量排序
5. 更新 index.yaml 中的 installs / unique_users 字段
6. 更新 README.md Top 10 列表
7. 自动 commit
```

### Skill 和 IP 统计方式完全一致

无论是 skill 还是 IP 包，安装后都通过同一机制（issue comment + reaction）计数。

---

## 十、搜索

```bash
ipman hub search scraper           # 关键词搜索
ipman hub search --agent openclaw  # 按 agent 过滤
ipman hub top                      # 显示 Top 排名
ipman hub info web-scraper         # 查看详细信息
```

搜索实现：
1. 拉取 index.yaml（可缓存，定期刷新）
2. 本地过滤匹配
3. 无需 GitHub Search API

---

## 十一、技术总结

| 需求 | 实现方式 |
|------|---------|
| 数据存储 | YAML 文件 in GitHub repo |
| 名称注册 | index.yaml（自动生成，短名称全局唯一） |
| Skill 版本 | 无语义化版本（history 记录 commit hash + 日期） |
| IP 包版本 | 分文件存储（meta.yaml + N.N.N.yaml），真正的版本控制 |
| 身份认证 | GitHub PR author（gh CLI token） |
| 权限控制 | CI 校验 PR author == namespace |
| 发布 | ipman hub publish → 自动提 PR |
| 安装 | 双模式：IpHub 引用 / 直接安装源 |
| 下载统计 | GitHub Issues (comment + reaction) |
| 排名 | 定时 Action 汇总 → README Top 10 |
| 搜索 | 本地 index.yaml 过滤 |
| 运维成本 | 零（纯 GitHub 原生能力） |
