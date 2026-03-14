# 当前 Sprint

**Sprint 6 - 风险评估引擎 + 配置文件**

**目标：** 实现配置文件加载、技能风险评估引擎、安全模式、安全日志

**状态：** 进行中

---

## 前置条件

- [x] Sprint 5 已完成并存档
- [x] PRD v2.0 安全需求已确认 (FR-S1 ~ FR-S9)
- [x] PyPI Trusted Publisher 已配置 (H06)
- [x] GitHub Pages 已启用 (H07)
- [x] CNB 镜像仓库已创建 (H08)

---

## 任务列表

| 优先级 | 任务 | 所属模块 | 责任人 | 状态 |
|-------|------|----------|--------|------|
| P0 | 实现配置文件加载 (`~/.ipman/config.yaml`) | core/config | AI | 待开始 |
| P0 | 实现风险评估引擎（红旗检测 + 权限分析 + 风险分级） | core/vetter | AI | 待开始 |
| P1 | 实现安全模式（PERMISSIVE/DEFAULT/CAUTIOUS/STRICT） | core/security | AI | 待开始 |
| P1 | 实现安全日志 (`~/.ipman/security.log`) | core/security | AI | 待开始 |
| P2 | 编写风险评估 + 配置 + 安全模式测试 | tests | AI | 进行中 |

---

## 模块状态

| 模块 | 状态 | 最后更新 | 当前目标 | 备注 |
|------|------|---------|---------|------|
| core/config | 待开始 | -- | YAML 配置加载 + 优先级合并 | 新模块 |
| core/vetter | 待开始 | -- | 红旗检测 + 风险分级 | 新模块 |
| core/security | 待开始 | -- | 安全模式 + 日志 | 新模块 |

---

## 近期改动记录

| 时间 | 改动目的 | 涉及模块/文件 |
|------|---------|-------------|
| 2026-03-14 | Sprint 6 初始化 | .claude/current-sprint.md |
