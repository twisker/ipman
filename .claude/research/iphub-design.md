# IpHub 设计方案

**设计日期：** 2026-03-14

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
│   │   ├── web-scraper.yaml        # Skill 注册
│   │   └── frontend-toolkit.yaml   # IP 包注册
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

### 3.1 Skill 注册文件

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
    install_type: plugin
    source: "web-scraper@twisker-plugins"
    marketplace: "https://github.com/twisker/twisker-plugins"  # claude marketplace 源
  openclaw:
    install_type: skill
    source: "web-scraper"
    hub: "https://clawhub.com"          # 缺省值，可指向非官方 hub

versions:
  - version: "1.2.0"
    released: 2026-03-10
    depends: [http-client]
    agents:
      claude-code:
        source: "web-scraper@twisker-plugins"
        min_version: "1.0.0"            # agent 最低版本要求
      openclaw:
        source: "web-scraper"
        hub: "https://clawhub.com"
  - version: "1.1.0"
    released: 2026-02-15
    depends: [http-client]
    agents:
      claude-code:
        source: "web-scraper@twisker-plugins"
      openclaw:
        source: "web-scraper"
```

### 3.2 IP 包注册文件

```yaml
# registry/@twisker/frontend-toolkit.yaml
type: ip
name: frontend-toolkit
description: "Essential skills for frontend development"
author: "@twisker"
license: MIT
homepage: https://github.com/twisker/frontend-toolkit

versions:
  - version: "1.0.0"
    released: 2026-03-14
    skills:
      - name: css-helper
        version: ">=2.0"
      - name: react-patterns
        version: "^1.3.0"
      - name: a11y-checker
        version: "*"
```

### 3.3 Agent 安装源配置

每个 agent 的安装源可以指定自定义地址：

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
    latest: "1.2.0"
    description: "Browser automation for web scraping"
    agents: [claude-code, openclaw]
    counter_issue: 42
    installs: 1234
    unique_users: 567
  git-helper:
    owner: "@alice"
    type: skill
    latest: "2.0.1"
    description: "Git workflow automation"
    agents: [claude-code]
    counter_issue: 43
    installs: 890
    unique_users: 234

packages:
  frontend-toolkit:
    owner: "@twisker"
    type: ip
    latest: "1.0.0"
    description: "Essential skills for frontend development"
    counter_issue: 44
    installs: 456
    unique_users: 123
```

### 短名称规则

| 规则 | 说明 |
|------|------|
| 全局唯一 | 不同 namespace 下也不能重名 |
| 先到先得 | 首个注册者拥有该短名称 |
| 不可转让 | 短名称绑定 owner（除非 owner 主动放弃） |
| 命名规范 | 小写字母 + 数字 + 连字符，3-50 字符 |
| Skill 和 IP 共享命名空间 | skill 和 IP 之间也不能重名 |

---

## 五、发布流程

### 5.1 发布 Skill

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

### 5.2 发布 IP 包

```
ipman hub publish frontend-toolkit.ip.yaml

  1. 读取本地 GitHub 身份
  2. 校验：引用的所有 skill 在 index.yaml 中存在
  3. Fork iphub 仓库
  4. 创建 registry/@twisker/frontend-toolkit.yaml
  5. 提 PR → CI 校验 → 自动合并
  6. Post-merge Action 更新 index + 创建 counter issue
```

---

## 六、安装流程

### 6.1 安装 Skill

```
ipman install web-scraper

  1. 拉取 index.yaml → 查找 web-scraper
  2. 读取 registry/@twisker/web-scraper.yaml
  3. 检测当前 agent（如 claude-code）
  4. 读取 agents.claude-code 配置:
       install_type: plugin
       source: "web-scraper@twisker-plugins"
       marketplace: "https://github.com/twisker/twisker-plugins"
  5. 执行 agent CLI 命令:
       claude plugin marketplace add twisker-plugins \
         https://github.com/twisker/twisker-plugins
       claude plugin install web-scraper@twisker-plugins
  6. 安装成功 → 向 counter issue 添加 comment + reaction
```

### 6.2 安装 IP 包

```
ipman install frontend-toolkit

  1. 拉取 index.yaml → 类型=ip
  2. 读取 registry/@twisker/frontend-toolkit.yaml
  3. 解析依赖列表: css-helper, react-patterns, a11y-checker
  4. 版本解析 + 递归依赖解析
  5. 逐一执行 ipman install <skill-name>（复用 skill 安装流程）
  6. 向 frontend-toolkit 的 counter issue 添加 comment + reaction
```

### 6.3 安装时的名称解析

```bash
ipman install web-scraper              # 短名称 → 查 index.yaml
ipman install @twisker/web-scraper     # 全名 → 直接定位
ipman install web-scraper --owner alice # 显式指定 owner（若短名称被占，用于装非注册版本）
```

---

## 七、身份认证与权限

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

## 八、安装统计

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

## 九、搜索

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

## 十、技术总结

| 需求 | 实现方式 |
|------|---------|
| 数据存储 | YAML 文件 in GitHub repo |
| 名称注册 | index.yaml（自动生成，短名称全局唯一） |
| 身份认证 | GitHub PR author（gh CLI token） |
| 权限控制 | CI 校验 PR author == namespace |
| 发布 | ipman hub publish → 自动提 PR |
| 安装 | ipman install → 解析引用 → 调用 agent CLI |
| 下载统计 | GitHub Issues (comment + reaction) |
| 排名 | 定时 Action 汇总 → README Top 10 |
| 搜索 | 本地 index.yaml 过滤 |
| 运维成本 | 零（纯 GitHub 原生能力） |
