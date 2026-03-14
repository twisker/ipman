# Sprint 7 存档

**Sprint 7 - 安装安全集成 + IpHub 举报 + 镜像**

**目标：** 将安全模块集成到 install/publish 命令，实现举报功能和镜像支持

**状态：** 已完成

**完成日期：** 2026-03-14

---

## 任务列表

| 优先级 | 任务 | 状态 |
|-------|------|------|
| P0 | install 命令集成安全策略（--security/--vet/--no-vet/--yes） | 已完成 |
| P0 | publish 命令集成发布时风险评估（阻止 HIGH/EXTREME） | 已完成 |
| P1 | `ipman hub report` 举报命令 | 已完成 |
| P1 | IpHub 镜像支持（config hub.url 驱动） | 已完成 |
| P2 | CNB 镜像同步工作流模板 | 已完成 |

**Sprint 7 新增测试：14 tests（项目总计 242 tests）**

---

## 关键设计决策

1. **install 安全路由**：本地/URL → 强制 vet；IpHub → 信任标注（除 STRICT 模式或 --vet）
2. **publish 门禁**：HIGH/EXTREME 直接阻止，无绕过选项
3. **举报通过 gh issue create** 提交到 iphub 仓库
4. **镜像通过 base_url** 参数传播到 IpHubClient 的所有 URL 构建
