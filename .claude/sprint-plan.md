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

### Sprint 2（Agent CLI 适配 + IpHub 客户端基础）

> **设计原则变更（Sprint 1 期间确认）：**
> - 所有 skill CRUD 通过 agent CLI 命令执行，不直接操作 agent 内部目录
> - IpHub 只存引用不存内容，安装通过 agent CLI 原生命令完成
> - 详见 `.claude/research/agent-skill-cli-comparison.md` 和 `.claude/research/iphub-design.md`

| 优先级 | 任务 | 所属模块 | 责任人 | 状态 |
|-------|------|----------|--------|------|
| P0 | 扩展 Agent 适配器接口：添加 skill install/uninstall/list 的 CLI 命令封装 | agents/base | AI | 已完成 |
| P0 | 实现 Claude Code 适配器的 skill CLI 封装（plugin install/uninstall/list） | agents/claude_code | AI | 已完成 |
| P0 | 实现 OpenClaw 适配器（clawhub install/uninstall、skill list） | agents/openclaw | AI | 已完成 |
| P1 | 实现 `ipman install <name>` 命令（通过 agent CLI 安装） | CLI + core | AI | 已完成 |
| P1 | 实现 `ipman uninstall <name>` 命令（通过 agent CLI 卸载） | CLI + core | AI | 已完成 |
| P1 | 实现 `ipman skill list` 命令（通过 agent CLI 列出） | CLI + core | AI | 已完成 |
| P1 | 实现 IpHub index.yaml 客户端读取与缓存 | hub/client | AI | 已完成 |
| P2 | 实现 `--agent` 参数覆盖自动探测 | CLI | AI | 已完成 |
| P2 | 编写 Agent 适配器 CLI 封装测试（mock subprocess） | tests | AI | 已完成 |
| P2 | 编写 IpHub 客户端测试 | tests | AI | 已完成 |

---

## Phase 2 -- IP 包管理

**目标：** 实现 IP 包格式定义、打包/解包、依赖解析

> Sprint 拆分待 Phase 1 完成后细化。

### Sprint 3（IP 包格式 + 打包）

| 优先级 | 任务 | 所属模块 | 责任人 | 状态 |
|-------|------|----------|--------|------|
| P0 | 定义 IP 包 YAML schema | core/package | AI | 已完成 |
| P0 | 实现 IP 包解析器 | core/package | AI | 已完成 |
| P0 | 实现 `ipman pack` 命令（合并原 export） | CLI + core | AI | 已完成 |
| P1 | 实现 `ipman install <file.ip.yaml>` 本地 IP 文件安装 | CLI + core | AI | 已完成 |
| P1 | 实现 `ipman install <short-name>` 基于 IpHub 的在线安装 | CLI + hub + core | AI | 已完成 |
| P1 | 实现依赖解析引擎（版本匹配 + 递归依赖 + 循环检测） | core/resolver | AI | 已完成 |
| P2 | 编写 IP 包管理测试（63 tests） | tests | AI | 已完成 |

---

## Phase 3 -- IpHub

**目标：** 实现 IpHub 搜索、下载、发布功能

### Sprint 4（IpHub 搜索 + 发布）

| 优先级 | 任务 | 所属模块 | 责任人 | 状态 |
|-------|------|----------|--------|------|
| P0 | 实现 `ipman hub search <query>` 命令 | cli/hub | AI | 已完成 |
| P0 | 实现 `ipman hub info <name>` 命令 | cli/hub | AI | 已完成 |
| P1 | 实现 `ipman hub top` 命令 | cli/hub | AI | 已完成 |
| P1 | 实现发布引擎 hub/publisher.py | hub/publisher | AI | 已完成 |
| P1 | 实现 `ipman hub publish <name>` Skill 发布 | cli/hub + hub/publisher | AI | 已完成 |
| P1 | 实现 `ipman hub publish <file.ip.yaml>` IP 包发布 | cli/hub + hub/publisher | AI | 已完成 |
| P2 | 安装统计上报（counter issue comment + reaction） | hub/stats | AI | 已完成 |
| P2 | 编写 IpHub CLI + publisher 测试（26 tests） | tests | AI | 已完成 |

---

## Phase 4 -- 打磨与发布

**目标：** 代码质量收尾、文档完善、PyPI 首次发布

### Sprint 5（代码质量 + 发布准备）

| 优先级 | 任务 | 所属模块 | 责任人 | 状态 |
|-------|------|----------|--------|------|
| P0 | `_resolve_agent` 去重提取到公共模块 | utils | AI | 已完成 |
| P0 | pyproject.toml 发布配置完善（动态版本） | 基础设施 | AI | 已完成 |
| P1 | ruff + mypy 全量检查修复 | 代码质量 | AI | 已完成 |
| P1 | README.md 更新 | docs | AI | 已完成 |
| P2 | GitHub Actions 发布工作流 | CI/CD | AI | 已完成 |

---

## Phase 5 -- 安全与配置

**目标：** 技能风险评估、安装安全策略、配置文件、IpHub 镜像

> 需求来源：PRD v2.0 第7节（FR-S1 ~ FR-S9）

### Sprint 6（风险评估引擎 + 配置文件）

| 优先级 | 任务 | 所属模块 | 责任人 | 状态 |
|-------|------|----------|--------|------|
| P0 | 实现配置文件加载 (`~/.ipman/config.yaml`) | core/config | AI | 已完成 |
| P0 | 实现风险评估引擎（红旗检测 + 权限分析 + 风险分级） | core/vetter | AI | 已完成 |
| P1 | 实现安全模式（PERMISSIVE/DEFAULT/CAUTIOUS/STRICT） | core/security | AI | 已完成 |
| P1 | 实现安全日志 (`~/.ipman/security.log`) | core/security | AI | 已完成 |
| P2 | 编写风险评估 + 配置 + 安全模式测试（52 tests） | tests | AI | 已完成 |

### Sprint 7（安装安全集成 + IpHub 举报 + 镜像）

| 优先级 | 任务 | 所属模块 | 责任人 | 状态 |
|-------|------|----------|--------|------|
| P0 | install 命令集成安全策略（--security/--vet/--no-vet/--yes） | cli/skill | AI | 已完成 |
| P0 | publish 命令集成发布时风险评估（阻止 HIGH/EXTREME） | cli/hub | AI | 已完成 |
| P1 | `ipman hub report` 举报命令 | cli/hub | AI | 已完成 |
| P1 | IpHub 镜像支持（config hub.url 驱动） | hub/client | AI | 已完成 |
| P2 | CNB (cnb.cool) 镜像同步工作流模板 | CI/CD | AI | 已完成 |
| P2 | 安装安全集成 + 举报测试（14 tests） | tests | AI | 已完成 |

---

## Phase 6 -- 国际化与分发

**目标：** 多语言支持、文档翻译、多渠道分发、主页动态内容

### Sprint 8（国际化 + 文档完善）

| 优先级 | 任务 | 所属模块 | 责任人 | 状态 |
|-------|------|----------|--------|------|
| P0 | i18n 模块（LANG 检测 + 中英文消息目录） | utils/i18n | AI | 已完成 |
| P0 | CLI 入口初始化 i18n | cli/main | AI | 已完成 |
| P1 | MkDocs 中文文档（首页/安装/快速上手/安全） | docs-src/zh | AI | 已完成 |
| P2 | README Star History 趋势图 | README | AI | 已完成 |
| P2 | README Roadmap + test count 更新 | README | AI | 已完成 |

### Sprint 9（多渠道分发）

| 优先级 | 任务 | 所属模块 | 责任人 | 状态 |
|-------|------|----------|--------|------|
| P1 | curl+sh 一键安装脚本（Unix-like） | scripts/install.sh | AI | 待开始 |
| P1 | Windows PyInstaller 打包（.exe） | CI/CD | AI | 待开始 |
| P2 | Windows 安装包（.msi 或 Inno Setup） | CI/CD | AI | 待开始 |
| P2 | GitHub Actions 发布时自动构建多平台二进制 | CI/CD | AI | 待开始 |
