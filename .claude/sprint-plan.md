# Sprint 计划

本文件记载此项目计划中需要经历的各个阶段（Sprint），以及每个 Sprint 中的任务项。每个 Sprint 要有整体目标描述和截止日期，其任务项必须详细拆分，精确描述，且应该指定优先级，以表格形式列出。后续根据开发进度，持续更新任务当前状态。

> **责任人说明：** 标记为"人工"的任务需要人工介入处理，与根目录 `人工TODO事项.md` 双向同步。标记为"AI"的任务由 AI 独立完成。

---

## Sprint 0（项目初始化）

**目标：** 建立开发框架，搭建 Python 项目骨架、CI/CD 流水线、测试框架

**截止：** 待定

### 任务拆分

| 优先级 | 任务 | 所属模块 | 责任人 | 状态 |
|-------|------|----------|--------|------|
| P0 | 初始化 pyproject.toml（uv 项目配置） | 基础设施 | AI | 已完成 |
| P0 | 创建 src/ipman 包目录结构 | 基础设施 | AI | 已完成 |
| P0 | 配置 ruff（lint + 格式化） | 基础设施 | AI | 已完成 |
| P0 | 配置 mypy（类型检查） | 基础设施 | AI | 已完成 |
| P0 | 配置 pytest（测试框架） | 测试 | AI | 已完成 |
| P1 | 实现 Click CLI 主入口（`ipman --help`） | CLI | AI | 已完成 |
| P1 | 搭建 GitHub Actions CI（三平台测试矩阵） | CI/CD | AI | 已完成 |
| P1 | 创建 GitHub 仓库描述和标签 | 基础设施 | 人工 | 已完成 |

---

## Phase 1 -- 核心功能（虚拟环境 + 技能管理）

**目标：** 实现 CLI 骨架、虚拟环境的创建/激活/删除、基本技能的安装/卸载

### Sprint 1（虚拟环境管理）

| 优先级 | 任务 | 所属模块 | 责任人 | 状态 |
|-------|------|----------|--------|------|
| P0 | 设计虚拟环境数据结构（目录布局、元数据格式） | core/environment | AI | 已完成 |
| P0 | 实现跨平台软链接工具函数 | utils/symlink | AI | 已完成 |
| P0 | 实现 `ipman create` 命令（project/user/machine scope） | CLI + core | AI | 已完成 |
| P0 | 实现 `ipman activate` / `ipman deactivate` 命令 | CLI + core | AI | 已完成 |
| P1 | 实现 `ipman delete` 命令 | CLI + core | AI | 已完成 |
| P1 | 实现 `ipman list` 命令（列出所有环境） | CLI + core | AI | 已完成 |
| P1 | 实现命令行提示符变更（环境激活标识） | core/environment | AI | 已完成 |
| P2 | 编写虚拟环境管理单元测试 | tests | AI | 已完成 |
| P2 | 编写虚拟环境管理集成测试 | tests | AI | 已完成 |

### Sprint 2（Agent 适配 + 技能管理基础）

| 优先级 | 任务 | 所属模块 | 责任人 | 状态 |
|-------|------|----------|--------|------|
| P0 | 设计 Agent 适配器基类接口 | agents/base | AI | 待开始 |
| P0 | 实现 Claude Code 适配器 | agents/claude_code | AI | 待开始 |
| P0 | 实现 Agent 工具自动探测 | utils/detect | AI | 待开始 |
| P1 | 实现 `ipman install <skill>` 命令（本地安装） | CLI + core | AI | 待开始 |
| P1 | 实现 `ipman uninstall <skill>` 命令 | CLI + core | AI | 待开始 |
| P1 | 实现 `ipman skill list` 命令（列出已安装技能） | CLI + core | AI | 待开始 |
| P2 | 实现 `--agent` 参数覆盖自动探测 | CLI | AI | 待开始 |
| P2 | 实现 `--inherit` 参数继承已有技能 | CLI + core | AI | 待开始 |
| P2 | 调研 OpenClaw 技能目录结构 | 调研 | AI | 待开始 |
| P2 | 编写 Agent 适配器和技能管理测试 | tests | AI | 待开始 |

---

## Phase 2 -- IP 包管理

**目标：** 实现 IP 包格式定义、打包/解包、依赖解析

> Sprint 拆分待 Phase 1 完成后细化。

### Sprint 3（IP 包格式 + 打包）

| 优先级 | 任务 | 所属模块 | 责任人 | 状态 |
|-------|------|----------|--------|------|
| P0 | 定义 IP 包 YAML schema | core/package | AI | 待开始 |
| P0 | 实现 IP 包解析器 | core/package | AI | 待开始 |
| P0 | 实现 `ipman pack` 命令 | CLI + core | AI | 待开始 |
| P1 | 实现 `ipman unpack` / `ipman install <ip-file>` | CLI + core | AI | 待开始 |
| P1 | 实现依赖解析引擎 | core/resolver | AI | 待开始 |
| P1 | 实现 `ipman export` 命令（导出当前环境为 IP 文件） | CLI + core | AI | 待开始 |
| P2 | 编写 IP 包管理测试 | tests | AI | 待开始 |

---

## Phase 3 -- IpHub

**目标：** 实现 IpHub 搜索、下载、发布功能

> Sprint 拆分待 Phase 2 完成后细化。

---

## Phase 4 -- 打磨与发布

**目标：** 国际化、完整文档、Windows 安装包、PyPI 首次发布

> Sprint 拆分待 Phase 3 完成后细化。
