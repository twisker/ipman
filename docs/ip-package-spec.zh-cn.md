# Intelligence Package (IP) 文件规格说明

本文档定义 IpMan 使用的 `.ip.yaml` 文件格式与语义。

## 概述

IP 文件是一个**技能清单** — 一个 YAML 文件，声明了一组要安装的技能，以及元数据和对其他 IP 包的依赖。任何人拿到 IP 文件，都可以通过 `ipman install <文件名>.ip.yaml` 一键安装所有引用的技能。

## 文件结构

```yaml
# IpMan Intelligence Package — https://github.com/twisker/ipman
# 安装: ipman install <本文件>.ip.yaml

name: <包名>
version: "<语义化版本>"
description: "<简要描述>"
author:
  name: "<作者名>"
  github: "@<GitHub用户名>"
license: <许可证标识>

skills:
  - name: <技能名>
  # ... 更多技能

dependencies:
  - name: <IP包名>
    version: "<版本约束>"
  # ... 更多依赖
```

## 头部注释

IpMan 自动生成的 IP 文件会包含头部注释：
- 指向 IpMan 项目代码库的链接
- 一行安装命令

确保任何拿到 IP 文件的人都知道如何使用。

## 字段说明

### 包元数据

| 字段 | 必填 | 说明 |
|------|------|------|
| `name` | 是 | 包短名称（小写字母 + 数字 + 连字符，3-50 字符） |
| `version` | 是 | 本 IP 包的语义化版本（major.minor.patch） |
| `description` | 是 | 技能集合的简要描述 |
| `author` | 否 | 作者信息（`name` 和/或 `github`） |
| `license` | 否 | 许可证标识（如 MIT、Apache-2.0） |

### 技能列表（skills）

`skills` 列表声明要安装的技能。每个条目支持两种模式：

#### IpHub 模式（推荐）

通过 IpHub 上注册的短名称引用技能：

```yaml
skills:
  - name: web-scraper
  - name: css-helper
```

安装时，IpMan 通过 IpHub 索引解析名称，获取 agent 安装源，调用 agent 原生 CLI 命令安装。

> **注意：** 技能没有版本约束。Agent CLI 安装的永远是源头最新版。安装版本由 agent 原生市场/hub 决定。

#### 直接安装源模式

直接指定 agent 安装参数，跳过 IpHub：

```yaml
skills:
  - name: our-internal-tool
    description: "可选描述"
    source:
      claude-code:
        plugin: "our-tool@our-marketplace"
        marketplace: "https://github.com/ourorg/claude-plugins"
      openclaw:
        slug: "our-internal-tool"
        hub: "https://internal-hub.ourorg.com"
```

适用场景：
- 未发布到 IpHub 的私有/内部技能
- 托管在非默认市场或 hub 上的技能

安装程序自动识别模式：有 `source` 字段用直接模式，无则用 IpHub 模式。

#### 直接安装源字段

**Claude Code：**

| 字段 | 必填 | 说明 |
|------|------|------|
| `plugin` | 是 | 插件标识（如 `name@marketplace`） |
| `marketplace` | 否 | 自定义 marketplace GitHub 仓库 URL |

**OpenClaw：**

| 字段 | 必填 | 说明 |
|------|------|------|
| `slug` | 是 | ClawHub 上的技能 slug |
| `hub` | 否 | 自定义 ClawHub URL（默认：`https://clawhub.com`） |

### 依赖列表（dependencies）

`dependencies` 列表声明需要先安装的其他 IP 包。同样支持两种模式：

#### IpHub 模式

```yaml
dependencies:
  - name: base-utils
    version: ">=1.0.0"
```

IP 包的版本是完全可控的 — IpHub 为每个版本存储独立文件。版本约束会匹配 IpHub 上的可用版本。

#### 直接安装源模式

```yaml
dependencies:
  # 本地文件
  - name: team-toolkit
    source: "./team-toolkit.ip.yaml"

  # 远程 URL
  - name: shared-skills
    source: "https://example.com/shared.ip.yaml"
```

直接指向 `.ip.yaml` 文件（本地路径或 URL）。文件本身即特定版本，无需 `version` 字段。

#### 版本约束语法

版本约束**仅适用于 IpHub IP 包依赖**（不适用于技能）。

| 语法 | 含义 |
|------|------|
| `>=1.2.0` | 大于等于 1.2.0 |
| `^1.3.0` | 兼容更新（>=1.3.0, <2.0.0） |
| `~1.3.0` | 仅补丁更新（>=1.3.0, <1.4.0） |
| `1.2.0` | 精确版本 |

## 完整示例

```yaml
# IpMan Intelligence Package — https://github.com/twisker/ipman
# 安装: ipman install frontend-kit.ip.yaml

name: frontend-kit
version: "2.0.0"
description: "前端开发技能集合"
author:
  name: "Twisker"
  github: "@twisker"
license: MIT

skills:
  # 公开技能（IpHub）
  - name: css-helper
  - name: a11y-checker

  # 私有技能（直接安装源）
  - name: our-design-system
    description: "内部设计系统技能"
    source:
      claude-code:
        plugin: "design-system@our-plugins"
        marketplace: "https://github.com/ourorg/claude-plugins"
      openclaw:
        slug: "our-design-system"
        hub: "https://internal-hub.ourorg.com"

dependencies:
  # 公开 IP 包（IpHub，版本约束有效）
  - name: base-utils
    version: ">=1.0.0"

  # 内部 IP 文件（直接安装源）
  - name: team-standards
    source: "https://raw.githubusercontent.com/ourorg/ips/main/standards.ip.yaml"
```

## 安装行为

```bash
# 从本地 IP 文件安装
ipman install frontend-kit.ip.yaml

# 从 URL 安装
ipman install https://example.com/frontend-kit.ip.yaml
```

安装程序执行流程：
1. 解析 IP 文件
2. 解析所有依赖（递归展开，循环检测）
3. 汇总所有技能（去重）
4. 通过对应 agent CLI 逐一安装每个技能
