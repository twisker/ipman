# Sprint 1 - 虚拟环境管理（已完成）

**目标：** 设计并实现虚拟环境的创建/激活/停用/删除/列表功能

**完成日期：** 2026-03-14

## 完成任务

| 优先级 | 任务 | 所属模块 | 状态 |
|-------|------|----------|------|
| P0 | 设计虚拟环境数据结构（目录布局、元数据格式） | core/environment | 已完成 |
| P0 | 实现跨平台软链接工具函数 | utils/symlink | 已完成 |
| P0 | 实现 `ipman create` 命令（project/user/machine scope） | CLI + core | 已完成 |
| P0 | 实现 `ipman activate` / `ipman deactivate` 命令 | CLI + core | 已完成 |
| P1 | 实现 `ipman delete` 命令 | CLI + core | 已完成 |
| P1 | 实现 `ipman list` 命令（列出所有环境） | CLI + core | 已完成 |
| P1 | 实现命令行提示符变更（环境激活标识） | core/environment | 已完成 |
| P2 | 编写虚拟环境管理单元测试 | tests | 已完成 |
| P2 | 编写虚拟环境管理集成测试 | tests | 已完成 |

## 关键设计决策

- **软链接即接口**：Agent 配置目录（如 `.claude/`）作为软链接指向 `.ipman/envs/<name>/`
- **备份机制**：激活时将已有配置目录备份为 `.claude.bak/`，停用时恢复
- **Prompt Tag**：`[ip:<machine><user><project>]` 格式，`*`=machine, `-`=user, 全名=project
- **Agent 适配器架构**：ABC 基类 + 具体适配器 + 注册表模式

## 测试覆盖

53 个测试全部通过（30 core/environment + 10 symlink + 10 cli/env + 3 cli/main）
