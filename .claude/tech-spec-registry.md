# 技术规格登记表

本文件记载此项目各模块使用的技术栈、技术规格。

---

## 1. 技术栈

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| 语言 | Python 3.10+ | 项目核心语言，确保跨平台兼容 |
| 包管理 | uv | 现代 Python 包管理器，使用 pyproject.toml |
| CLI 框架 | Click | 成熟的命令行框架，支持子命令、自动帮助生成 |
| 测试框架 | pytest | 单元测试 + 集成测试 |
| 代码质量 | ruff | Lint + 格式化 |
| 类型检查 | mypy | 静态类型检查，strict 模式 |
| 文档生成 | MkDocs + mkdocs-material | Markdown 源文件构建为 HTML 文档站 |
| CI/CD | GitHub Actions | 跨平台构建、测试、发布 |
| 发布渠道 | PyPI | `pip install ipman` / `uv pip install ipman` |
| 打包 | PyInstaller | Windows 预编译可执行文件 |
| IP 包格式 | YAML | 支持注释，可读性强，适合技能包定义 |

---

## 2. 配色体系

不适用（CLI 工具，无 Web 界面）。

终端输出配色规范：

| 用途 | 颜色 | 说明 |
|------|------|------|
| 成功 | 绿色 | 操作成功提示 |
| 警告 | 黄色 | 潜在问题提示 |
| 错误 | 红色 | 操作失败提示 |
| 信息 | 蓝色/白色 | 一般信息输出 |
| 环境标识 | 青色 | 命令行提示符中的环境名称 |

---

## 3. 布局规范

不适用（CLI 工具）。

CLI 输出规范：
- 表格输出使用 `rich` 或 `tabulate` 库
- 进度条使用 `rich.progress`
- 帮助文本遵循 Click 默认格式

---

## 4. 通用组件规范

不适用（无前端组件）。

---

## 5. 核心 API 依赖

| 接口 | 用途 | 状态 |
|------|------|------|
| Agent CLI | 通过 agent 原生命令安装/卸载 skill | 已调研（详见 `.claude/research/agent-skill-cli-comparison.md`） |
| GitHub API (gh CLI) | IpHub 引用注册表：发布 PR、计数 issue、读取 index | Phase 3 实现 |
| PyPI API | IpMan 自身发布 | Phase 4 实现 |

> **IpHub 设计文档**：详见 `.claude/research/iphub-design.md`
>
> 核心要点：IpHub 只存引用不存内容，安装通过 agent CLI 原生命令完成。
> 身份认证基于 GitHub PR author，短名称全局唯一。

---

## 6. 命令行提示符标签（Prompt Tag）设计

虚拟环境激活后，IpMan 在 shell 提示符前注入一个紧凑的标签，以直观反映三个作用域层级的激活状态。

### 格式

```
[ip:<machine><user><project_name>]
```

| 层级 | 激活时显示 | 未激活时 | 说明 |
|------|-----------|---------|------|
| Machine | `*` | 省略 | 全局机器级环境 |
| User | `-` | 省略 | 当前用户级环境 |
| Project | 环境全名 | 省略 | 项目级环境，显示完整名称 |

### 示例

| 标签 | 含义 |
|------|------|
| `[ip:*-myenv]` | 三层全部激活（machine + user + project "myenv"） |
| `[ip:myenv]` | 仅 project 层激活 |
| `[ip:*myenv]` | machine + project 激活 |
| `[ip:*-]` | machine + user 激活，无 project |
| `[ip:*]` | 仅 machine 层激活 |
| `[ip:-]` | 仅 user 层激活 |

### 详细状态查看

```bash
ipman env status
```

输出各层级激活环境的详细信息（名称、Agent、路径），适合排查问题或查看完整环境配置。

### 实现

- 核心函数：`ipman.core.environment.build_prompt_tag()`
- Shell 脚本生成：`generate_activate_script()` / `generate_deactivate_script()`
- 支持 bash/zsh、fish、powershell 三种 shell
- 激活时修改 `PS1`（bash/zsh）或 `fish_prompt`（fish）或 `prompt`（powershell）
- 停用时恢复原始提示符

### 文档要求

此 Prompt Tag 设计必须在以下文档中体现：
- 用户教程（Getting Started / Quick Start）
- `ipman env --help` 帮助文本
- MkDocs 文档站的 CLI 参考章节
- README.md 功能特性列表

---

## 7. 性能与安全要求

| 要求 | 说明 |
|------|------|
| 版本管理 | 遵循 major.minor.patch 格式，patch 自动递增，major/minor 人工触发 |
| 启动速度 | CLI 冷启动 < 500ms |
| 安装速度 | 单技能安装 < 5s（本地），< 15s（网络） |
| 跨平台 | Linux、macOS、Windows 三平台行为一致 |
| 软链接安全 | 创建软链接时校验路径合法性，防止路径穿越 |
| 依赖最小化 | 核心功能尽量减少外部依赖 |
