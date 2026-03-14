# Agent Skill CLI 命令调研对比

**调研日期：** 2026-03-14

---

## 一、Claude Code

### 概念模型

Claude Code 中没有独立的 "skill" 概念。Skills 是 **Plugin（插件）** 的一个子组件。

```
Plugin
├── .claude-plugin/
│   ├── plugin.json        # 插件清单（name, description, version, author, etc.）
│   └── marketplace.json   # 市场元数据
├── skills/                # 技能目录
│   └── <skill-name>/
│       └── SKILL.md       # 技能定义（YAML frontmatter + markdown 正文）
├── commands/              # 斜杠命令
├── agents/                # 子代理定义
├── hooks/                 # 钩子（PreToolUse, PostToolUse, etc.）
└── README.md
```

### CLI 命令

| 命令 | 说明 |
|------|------|
| `claude plugin install <name>` | 从市场安装插件 |
| `claude plugin install <name>@<marketplace>` | 从指定市场安装 |
| `claude plugin install -s <scope>` | 指定作用域（user/project/local） |
| `claude plugin uninstall <name>` | 卸载插件 |
| `claude plugin list` | 列出已安装插件 |
| `claude plugin list --json` | JSON 格式输出 |
| `claude plugin list --available` | 含市场可用插件（需 --json） |
| `claude plugin enable <name>` | 启用已禁用的插件 |
| `claude plugin disable <name>` | 禁用插件 |
| `claude plugin update <name>` | 更新插件 |
| `claude plugin validate <path>` | 验证插件结构 |
| `claude plugin marketplace add <source>` | 添加市场源 |
| `claude plugin marketplace list` | 列出市场源 |
| `claude plugin marketplace remove <name>` | 移除市场源 |
| `claude plugin marketplace update [name]` | 更新市场数据 |

### MCP 相关命令

| 命令 | 说明 |
|------|------|
| `claude mcp add <name> <cmd> [args...]` | 添加 MCP 服务器 |
| `claude mcp add --transport http <name> <url>` | 添加 HTTP MCP |
| `claude mcp add -e KEY=val <name> -- cmd` | 带环境变量 |
| `claude mcp list` | 列出 MCP 服务器 |
| `claude mcp get <name>` | 查看详情 |
| `claude mcp remove <name>` | 移除 MCP 服务器 |

### Skill 文件格式（SKILL.md）

```markdown
---
name: skill-name
description: "Skill description for triggering"
---

# Skill Title

Skill content in markdown...
```

### 存储位置

- **User scope:** `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`
- **Project scope:** `<project>/.claude/plugins/` (推测)

### 市场

- 官方市场: `anthropics/claude-plugins-official`（GitHub 仓库）
- 可添加自定义市场源（GitHub 仓库）

---

## 二、OpenClaw

### 概念模型

OpenClaw 中 **Skill（技能）** 是一等公民，独立存在。不需要包裹在 plugin 里。

```
<workspace>/skills/
└── <skill-name>/
    ├── SKILL.md           # 技能定义（YAML frontmatter + markdown 正文）
    └── (其他资源文件)
```

### CLI 命令

| 命令 | 说明 |
|------|------|
| `clawhub install <skill-slug>` | 从 ClawHub 安装技能到 workspace |
| `clawhub update --all` | 更新所有已安装技能 |
| `clawhub sync --all` | 扫描并发布更新 |

> 注：OpenClaw 核心 CLI 是 `openclaw`，技能市场 CLI 是 `clawhub`

### Skill 文件格式（SKILL.md）

```markdown
---
name: skill-name
description: Brief skill description
homepage: https://example.com
user-invocable: true
disable-model-invocation: false
metadata:
  openclaw:
    always: true
    emoji: "emoji"
    os: ["darwin", "linux", "win32"]
    requires:
      bins: ["binary_name"]
      env: ["ENV_VAR"]
    install: [...]
---

# Skill Content

Markdown content...
```

### 技能加载优先级（三层）

| 优先级 | 位置 | 说明 |
|--------|------|------|
| 最高 | `<workspace>/skills/` | 工作区技能（项目级） |
| 中 | `~/.openclaw/skills/` | 托管/本地技能（用户级） |
| 最低 | 内置技能 | 随安装包分发 |

额外：
- `skills.load.extraDirs` 配置额外加载目录
- Plugin skills 通过 `openclaw.plugin.json` 加载

### 配置方式

`~/.openclaw/openclaw.json`:
```json
{
  "skills": {
    "entries": {
      "skill-name": {
        "enabled": true,
        "env": { "VAR": "value" },
        "config": { "customKey": "value" }
      }
    }
  }
}
```

### 市场

- **ClawHub**（https://clawhub.com）— 公开技能注册表
- 截至 2026-02 有 13,729 个社区技能
- 支持自动搜索和拉取

---

## 三、对比总结

| 维度 | Claude Code | OpenClaw |
|------|-------------|----------|
| **技能单位** | Plugin（插件，包含 skills/commands/agents/hooks） | Skill（独立技能） |
| **技能格式** | SKILL.md（YAML frontmatter + markdown） | SKILL.md（YAML frontmatter + markdown） |
| **安装命令** | `claude plugin install <name>` | `clawhub install <slug>` |
| **卸载命令** | `claude plugin uninstall <name>` | (未明确文档) |
| **列表命令** | `claude plugin list` | (未明确文档) |
| **作用域** | user / project / local | workspace / user / bundled |
| **市场** | GitHub 仓库（marketplace） | ClawHub（独立注册表） |
| **市场规模** | ~25 个官方插件 | 13,729 个社区技能 |
| **CLI 工具** | `claude` 子命令 | `openclaw` + `clawhub` 两个 CLI |
| **元数据格式** | plugin.json（插件级） | SKILL.md frontmatter（技能级） |
| **加载机制** | 插件缓存目录 + 符号链接 | 三层目录优先级覆盖 |

---

## 四、对 IpMan 的影响

### 关键发现

1. **两者的 skill 定义格式高度相似**：都用 SKILL.md + YAML frontmatter + markdown 正文
2. **管理粒度不同**：Claude Code 以 plugin 为单位，OpenClaw 以 skill 为单位
3. **都有 CLI 命令**：可以通过 CLI 安装/卸载，而非直接操作文件
4. **都有市场/注册表**：Claude Code 用 GitHub 仓库，OpenClaw 用 ClawHub

### IpMan adapter 需要封装的命令

**Claude Code adapter:**
- 安装: `claude plugin install <name> -s <scope>`
- 卸载: `claude plugin uninstall <name>`
- 列表: `claude plugin list --json`
- 启用/禁用: `claude plugin enable/disable <name>`

**OpenClaw adapter:**
- 安装: `clawhub install <slug>`
- 卸载: (需进一步调研)
- 列表: (需进一步调研，可能通过读取 workspace/skills/ 目录)
- 更新: `clawhub update --all`

### IP 包的角色

IP 包应该是一个 **技能清单文件**，定义了一组要安装的技能及其来源：
- 对 Claude Code：列出要安装的 plugin 名称和来源
- 对 OpenClaw：列出要安装的 skill slug
- `ipman install <ip-file>` 读取清单，逐一调用 agent 的 CLI 命令安装
- `ipman uninstall <ip>` 逆向操作
