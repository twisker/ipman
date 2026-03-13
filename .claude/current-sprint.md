# 当前 Sprint

**Sprint 1 - 虚拟环境管理**

**目标：** 设计并实现虚拟环境的创建/激活/停用/删除/列表功能

---

## 任务列表

| 优先级 | 任务 | 所属模块 | 责任人 | 状态 |
|-------|------|----------|--------|------|
| P0 | 设计虚拟环境数据结构（目录布局、元数据格式） | core/environment | AI | 进行中 |
| P0 | 实现跨平台软链接工具函数 | utils/symlink | AI | 待开始 |
| P0 | 实现 `ipman create` 命令（project/user/machine scope） | CLI + core | AI | 待开始 |
| P0 | 实现 `ipman activate` / `ipman deactivate` 命令 | CLI + core | AI | 待开始 |
| P1 | 实现 `ipman delete` 命令 | CLI + core | AI | 待开始 |
| P1 | 实现 `ipman list` 命令（列出所有环境） | CLI + core | AI | 待开始 |
| P1 | 实现命令行提示符变更（环境激活标识） | core/environment | AI | 待开始 |
| P2 | 编写虚拟环境管理单元测试 | tests | AI | 待开始 |
| P2 | 编写虚拟环境管理集成测试 | tests | AI | 待开始 |

---

## 模块状态

| 模块 | 状态 | 最后更新 | 当前目标 | 备注 |
|------|------|---------|---------|------|
| core/environment | 改动中 | 2026-03-14 | 数据结构设计 | 待人工确认设计方案 |
| utils/symlink | 待开始 | -- | -- | -- |
| cli/env | 待开始 | -- | -- | -- |

---

## 活跃文件清单

- `.claude/current-sprint.md`
- (设计确认后将新增实现文件)

---

## 近期改动记录

| 时间 | 改动目的 | 涉及模块/文件 |
|------|---------|-------------|
| 2026-03-14 | Sprint 1 启动，Sprint 0 存档 | .claude/archive/sprint-0.md |
