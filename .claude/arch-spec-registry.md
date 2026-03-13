# 架构规格登记表

本文件记载项目的技术架构规格，包括环境规划、基础设施、部署方式、CI/CD 流水线等。

---

## 1. 架构总览

### 系统分层

| 层级 | 说明 | 核心技术 |
|------|------|---------|
| CLI 层 | 命令解析、参数校验、用户交互 | Click |
| 核心层 | 虚拟环境管理、技能管理、IP 包管理 | Python stdlib + pathlib |
| Agent 适配层 | 不同 Agent 工具的技能目录适配 | 插件式架构 |
| 市场层 | 在线市场交互、搜索、发布 | httpx + GitHub API |
| 存储层 | 本地元数据、锁定文件、环境配置 | YAML + SQLite(可选) |

### 核心设计原则

- **Agent 解耦**：不侵入 Agent 内部实现，仅通过软链接或标准接口操作
- **插件式适配**：每个 Agent 工具一个适配器，新增 Agent 支持不影响核心逻辑
- **依赖最小化**：核心功能尽量使用 Python 标准库，减少外部依赖
- **跨平台一致性**：所有路径操作使用 pathlib，软链接在 Windows 上有降级方案
- **快速解析**：借鉴 uv 的依赖解析思路，IP 包依赖解析应快速高效

---

## 2. 环境规划

### 环境矩阵

| 环境 | 标识 | 用途 | 发布方式 |
|------|------|------|---------|
| 本地开发 | `local` | 开发调试 | `uv run` 直接运行 |
| CI 测试 | `ci` | 跨平台自动测试 | GitHub Actions |
| PyPI 预发布 | `test-pypi` | 发布前验证 | `uv publish --index testpypi` |
| PyPI 正式 | `pypi` | 正式发布 | release 分支合并触发 |

---

## 3. CI/CD 流水线

### 流水线概览

| 触发条件 | 执行内容 | 部署目标 |
|---------|---------|---------|
| push to dev | Lint + 类型检查 + 单元测试（三平台） | 无 |
| push to release/* | 全量测试 + 构建 + 发布到 TestPyPI | TestPyPI |
| merge release to main | 全量测试 + 构建 + 发布到 PyPI + GitHub Release | PyPI |
| tag v*.*.* | 构建 Windows 可执行文件 + 发布到 GitHub Release | GitHub Release |

### CI 阶段（自动）

1. **代码质量**：ruff lint + mypy 类型检查
2. **测试**：pytest 单元测试 + 集成测试（Linux/macOS/Windows 矩阵）
3. **构建**：`uv build` 生成 wheel 和 sdist
4. **发布**：根据分支决定发布目标

### CD 阶段（手动）

- **PyPI 发布**：release 分支合并到 main 时自动触发
- **Windows 可执行文件**：tag 创建时通过 PyInstaller 构建

---

## 4. 可观测性

| 层级 | 工具 |
|------|------|
| CLI 日志 | Python logging，支持 `--verbose` / `--debug` 参数调节日志级别 |
| 安装统计 | GitHub-based 计数（Phase 3） |
| 错误追踪 | GitHub Issues（用户报告） |

---

## 5. 版本管理与发布

### 版本格式

`major.minor.patch`（如 `1.2.34`）

### 分支策略（Git Flow）

| 分支 | 用途 | 合并目标 |
|------|------|---------|
| `main` | 稳定发布版本 | -- |
| `dev` | 开发集成分支 | release/* |
| `feature/*` | 功能开发 | dev |
| `release/*` | 发布准备 | main + dev |
| `hotfix/*` | 紧急修复 | main + dev |

### 自动管理规则

| 版本段 | 更新方式 | 触发条件 |
|--------|---------|---------|
| patch | 自动（git hook） | 每次 git commit |
| minor | 人工脚本 | 人工调用 `scripts/bump-minor.sh` |
| major | 人工脚本 | 人工调用 `scripts/bump-major.sh` |

---

## 6. 项目目录结构

```
ipman/
├── src/
│   └── ipman/
│       ├── __init__.py          # 包入口，版本号
│       ├── cli/                 # CLI 命令定义（Click）
│       │   ├── __init__.py
│       │   ├── main.py          # 主入口 cli group
│       │   ├── env.py           # 虚拟环境命令（create/activate/deactivate/delete/list）
│       │   ├── skill.py         # 技能命令（install/uninstall/upgrade/list）
│       │   ├── pack.py          # IP 包命令（pack/unpack/export）
│       │   └── market.py        # 市场命令（search/publish/top）
│       ├── core/                # 核心业务逻辑
│       │   ├── __init__.py
│       │   ├── environment.py   # 虚拟环境管理
│       │   ├── skill.py         # 技能管理
│       │   ├── package.py       # IP 包解析与管理
│       │   ├── resolver.py      # 依赖解析
│       │   └── registry.py      # 本地元数据注册表
│       ├── agents/              # Agent 适配器
│       │   ├── __init__.py
│       │   ├── base.py          # 适配器基类
│       │   ├── claude_code.py   # Claude Code 适配
│       │   └── openclaw.py      # OpenClaw 适配
│       ├── market/              # 在线市场交互
│       │   ├── __init__.py
│       │   ├── client.py        # 市场 HTTP 客户端
│       │   └── publisher.py     # 发布逻辑
│       └── utils/               # 通用工具
│           ├── __init__.py
│           ├── symlink.py       # 跨平台软链接
│           ├── i18n.py          # 国际化
│           └── detect.py        # Agent 探测
├── tests/
│   ├── conftest.py
│   ├── test_cli/
│   ├── test_core/
│   ├── test_agents/
│   └── test_market/
├── docs/
│   ├── PRD.md
│   ├── PRD.zh-cn.md
│   ├── en/                      # 英文文档
│   └── zh-cn/                   # 中文文档
├── scripts/
│   ├── bump-patch.sh
│   ├── bump-minor.sh
│   └── bump-major.sh
├── .githooks/
│   └── pre-commit
├── .claude/
├── .github/
│   └── workflows/
├── pyproject.toml
├── VERSION
├── README.md
├── CLAUDE.md
└── LICENSE
```
