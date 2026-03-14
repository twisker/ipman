# Sprint 6 存档

**Sprint 6 - 风险评估引擎 + 配置文件**

**目标：** 配置文件加载、技能风险评估引擎、安全模式、安全日志

**状态：** 已完成

**完成日期：** 2026-03-14

---

## 任务列表

| 优先级 | 任务 | 状态 |
|-------|------|------|
| P0 | 配置文件加载 (`~/.ipman/config.yaml`) | 已完成 |
| P0 | 风险评估引擎（红旗检测 + 权限分析 + 风险分级） | 已完成 |
| P1 | 安全模式（PERMISSIVE/DEFAULT/CAUTIOUS/STRICT） | 已完成 |
| P1 | 安全日志 (`~/.ipman/security.log`) | 已完成 |
| P2 | 测试 | 已完成 |

---

## 模块状态

| 模块 | 测试数 | 备注 |
|------|--------|------|
| core/config | 12 | YAML 配置加载 + env 覆盖 + 优先级合并 |
| core/vetter | 21 | 红旗检测 + 元数据检查 + 风险分级 + 报告 |
| core/security | 19 | 4x4 决策矩阵 + 安全日志 |

**Sprint 6 新增测试：52 tests（项目总计 228 tests）**

---

## 关键设计决策

1. **IpManConfig frozen dataclass** — 配置加载后不可变
2. **RiskLevel 用 IntEnum** — 支持 max() 比较取最高风险
3. **Pattern 表驱动** — 新增检测规则只需加一行
4. **决策矩阵字典查表** — 避免 if/elif 链
