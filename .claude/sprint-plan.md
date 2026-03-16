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
| P1 | curl+sh 一键安装脚本 | scripts/install.sh | AI | 已完成 |
| P1 | iphub 定时统计 + README Top 排名 Action | CI/CD | AI | 已完成 |
| P1 | 多平台 PyInstaller 打包（Linux/macOS/Windows） | CI/CD | AI | 已完成 |
| P2 | GitHub Actions 发布时自动构建 + GitHub Release 上传 | CI/CD | AI | 已完成 |

---

## Phase 4 -- 用户体验改进 + 持续质量保障

### Sprint 7（activate/deactivate 脚本 + install 增强 + E2E 完善）

**目标：** 简化虚拟环境操作体验，扩展 install 命令，完善 E2E 测试覆盖

| 优先级 | 任务 | 所属模块 | 责任人 | 状态 |
|-------|------|----------|--------|------|
| P0 | 为各平台提供 activate/deactivate 脚本（参考 conda）：`ipman init` 命令注入 shell function wrapper，支持 bash/zsh/fish/powershell | core/shell_init + CLI | AI | 已完成 |
| P0 | 扩展 `ipman install` 支持直接安装本地 skill（自动检测类型：.ip.yaml / skill目录 / IpHub名称）。Claude Code 走 `claude plugin add ./path`（需 `.claude-plugin/plugin.json` 结构），OpenClaw 走文件复制到 skills 目录。需同步更新 `ClaudeCodeAdapter.install_skill()` 区分远程名称 vs 本地路径 | cli/skill + agents | AI | 待开始 |
| P0 | 更新 E2E test fixture 为正确的 plugin 结构（Claude Code: 添加 `.claude-plugin/plugin.json`；OpenClaw: 标准 skill 目录），解锁 3 个 skip 的 Layer 2 测试 | tests/e2e/fixtures + test_skill_install | AI | 待开始 |
| P1 | Shell 集成：`ipman init` 注入后 activate/deactivate 直接生效，含 `--reverse` 撤销 + `--dry-run` 预览 | core/shell_init + CLI | AI | 已完成 |
| P1 | Windows PowerShell 兼容：`Invoke-Expression` + 正确 splatting，替代不可用的 eval | core/shell_init | AI | 已完成 |
| P1 | 更新 `ClaudeCodeAdapter`：`install_skill()` 区分远程名称（`claude plugin install`）和本地路径（`claude plugin add`） | agents/claude_code | AI | 待开始 |
| P1 | 更新 `OpenClawAdapter`：`install_skill()` 对本地路径走文件复制到 `skills/` 目录 | agents/openclaw | AI | 待开始 |
| P2 | E2E 测试框架持续改进：根据运行结果修复测试用例 | tests/e2e | AI | 已完成 |

---

## Phase 5 -- IpHub Awesome-List 转型

> **总体目标：** 将 IpHub 从扁平注册表升级为 awesome-list 式的策展与传播平台
> **设计文档：** `docs/superpowers/specs/2026-03-16-iphub-ip-format-enhancement-design.md`
> **实施计划：** `docs/superpowers/plans/2026-03-16-iphub-ip-format-enhancement.md`

### Sprint 10（Sub-1: IP 格式增强 + 版本迭代 + Tag + 页面生成）

**目标：** 扩展 IP 数据模型，建立三层架构（yaml → md → html），支持 tag 搜索、趋势统计、i18n Landing Page

| 优先级 | 任务 | 所属模块 | 责任人 | 状态 |
|-------|------|----------|--------|------|
| P0 | IPPackage 扩展：新增 tags/summary/homepage/repository/icon/links 字段 | core/package | AI | 待开始 |
| P0 | Publisher 适配：registry 输出新字段 + 版本文件含 changelog | hub/publisher | AI | 待开始 |
| P0 | Client 适配：search() 支持 --tag 过滤 | hub/client | AI | 待开始 |
| P0 | CLI 适配：hub search --tag, hub info 展示新字段 | cli/hub | AI | 待开始 |
| P1 | i18n 翻译文件（en + zh-cn）| iphub/templates | AI | 待开始 |
| P1 | README.md 生成模板（含新手引导）| iphub/templates | AI | 待开始 |
| P1 | HTML Landing Page 模板（i18n + 响应式）| iphub/templates | AI | 待开始 |
| P1 | 页面生成脚本 generate_pages.py | iphub/scripts | AI | 待开始 |
| P1 | 趋势计算脚本 generate_trending.py | iphub/scripts | AI | 待开始 |
| P2 | rebuild-index.yml：tag 聚合 + 趋势 + Labels 同步 | iphub/CI | AI | 待开始 |
| P2 | rebuild-pages.yml：自动生成页面工作流 | iphub/CI | AI | 待开始 |
| P2 | validate-pr.yml：tag 格式校验 | iphub/CI | AI | 待开始 |
| P2 | GitHub Pages 启用（人工） | iphub 仓库设置 | 人工 | 待开始 |

### Sprint 11-13（Sub-2 ~ Sub-5：待设计）

| Sprint | 子项目 | 状态 |
|--------|--------|------|
| Sprint 11 | Sub-2: Tag 搜索 + 排名 + 趋势推荐系统 | 待设计 |
| Sprint 12 | Sub-3: 个人页面 + IP Landing Page 完善 | 待设计 |
| Sprint 13 | Sub-4: 社交媒体趋势抓取 + 自动 IP 生成 | 待设计 |
| Sprint 14 | Sub-5: 自动化编排层 | 待设计 |
