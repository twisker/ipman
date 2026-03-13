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
| Agent 技能目录 API | 读取/操作 Agent 工具的技能存放路径 | 待调研（需针对 OpenClaw、Claude Code 分别适配） |
| GitHub API | 在线市场数据存储（Issues/Pages） | Phase 3 实现 |
| PyPI API | IpMan 自身发布 | Phase 4 实现 |

---

## 6. 性能与安全要求

| 要求 | 说明 |
|------|------|
| 版本管理 | 遵循 major.minor.patch 格式，patch 自动递增，major/minor 人工触发 |
| 启动速度 | CLI 冷启动 < 500ms |
| 安装速度 | 单技能安装 < 5s（本地），< 15s（网络） |
| 跨平台 | Linux、macOS、Windows 三平台行为一致 |
| 软链接安全 | 创建软链接时校验路径合法性，防止路径穿越 |
| 依赖最小化 | 核心功能尽量减少外部依赖 |
