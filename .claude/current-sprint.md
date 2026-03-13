# 当前 Sprint

**Sprint 1 - 虚拟环境管理**

**目标：** 设计并实现虚拟环境的创建/激活/停用/删除/列表功能

**状态：** 已完成

---

## 任务列表

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

---

## 模块状态

| 模块 | 状态 | 最后更新 | 当前目标 | 备注 |
|------|------|---------|---------|------|
| core/environment | 已完成 | 2026-03-14 | -- | 含 prompt tag、env status |
| utils/symlink | 已完成 | 2026-03-14 | -- | 跨平台，含 Windows junction fallback |
| cli/env | 已完成 | 2026-03-14 | -- | create/activate/deactivate/delete/list/status |
| agents/base | 已完成 | 2026-03-14 | -- | AgentAdapter ABC |
| agents/claude_code | 已完成 | 2026-03-14 | -- | Claude Code 适配器 |
| agents/registry | 已完成 | 2026-03-14 | -- | 适配器注册与自动探测 |

---

## 活跃文件清单

- `src/ipman/core/environment.py`
- `src/ipman/utils/symlink.py`
- `src/ipman/cli/env.py`
- `src/ipman/agents/base.py`
- `src/ipman/agents/claude_code.py`
- `src/ipman/agents/registry.py`
- `tests/test_core/test_environment.py`
- `tests/test_core/test_symlink.py`
- `tests/test_cli/test_env.py`

---

## 近期改动记录

| 时间 | 改动目的 | 涉及模块/文件 |
|------|---------|-------------|
| 2026-03-14 | Sprint 1 启动，Sprint 0 存档 | .claude/archive/sprint-0.md |
| 2026-03-14 | 实现虚拟环境 CRUD + 软链接激活机制 | core/environment, utils/symlink |
| 2026-03-14 | 实现 CLI env 子命令（create/activate/deactivate/delete/list/status） | cli/env |
| 2026-03-14 | 实现 Agent 适配器架构（base + claude_code + registry） | agents/* |
| 2026-03-14 | 实现 prompt tag 设计（[ip:*-myenv] 格式） | core/environment |
| 2026-03-14 | 编写 53 个测试（全部通过） | tests/ |
| 2026-03-14 | Prompt tag 设计写入技术规格文档 | .claude/tech-spec-registry.md |
