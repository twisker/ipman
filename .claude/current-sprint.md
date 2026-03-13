# 当前 Sprint

**Sprint 2 - Agent CLI 适配 + IpHub 客户端基础**

**目标：** 基于 agent CLI 命令封装技能安装/卸载；实现 IpHub 引用注册表的客户端读取

**状态：** 待启动（等待人工确认）

---

## 前置条件

- [x] Sprint 1 已完成并存档
- [x] Agent CLI 调研完成（`.claude/research/agent-skill-cli-comparison.md`）
- [x] IpHub 设计方案确定（`.claude/research/iphub-design.md`）
- [ ] 人工确认开始 Sprint 2

---

## 任务列表

| 优先级 | 任务 | 所属模块 | 责任人 | 状态 |
|-------|------|----------|--------|------|
| P0 | 扩展 Agent 适配器接口：添加 skill install/uninstall/list 的 CLI 命令封装 | agents/base | AI | 待开始 |
| P0 | 实现 Claude Code 适配器的 skill CLI 封装（plugin install/uninstall/list） | agents/claude_code | AI | 待开始 |
| P0 | 实现 OpenClaw 适配器（clawhub install/uninstall、skill list） | agents/openclaw | AI | 待开始 |
| P1 | 实现 `ipman install <name>` 命令（通过 agent CLI 安装） | CLI + core | AI | 待开始 |
| P1 | 实现 `ipman uninstall <name>` 命令（通过 agent CLI 卸载） | CLI + core | AI | 待开始 |
| P1 | 实现 `ipman skill list` 命令（通过 agent CLI 列出） | CLI + core | AI | 待开始 |
| P1 | 实现 IpHub index.yaml 客户端读取与缓存 | hub/client | AI | 待开始 |
| P2 | 实现 `--agent` 参数覆盖自动探测 | CLI | AI | 待开始 |
| P2 | 编写 Agent 适配器 CLI 封装测试（mock subprocess） | tests | AI | 待开始 |
| P2 | 编写 IpHub 客户端测试 | tests | AI | 待开始 |

---

## 模块状态

| 模块 | 状态 | 最后更新 | 当前目标 | 备注 |
|------|------|---------|---------|------|
| agents/base | 待更新 | -- | 添加 skill CLI 方法 | Sprint 1 已有基类，需扩展 |
| agents/claude_code | 待更新 | -- | 封装 claude plugin CLI | Sprint 1 已有适配器，需扩展 |
| agents/openclaw | 待开始 | -- | 新建 OpenClaw 适配器 | |
| hub/client | 待开始 | -- | index.yaml 读取与缓存 | |
| cli/skill | 待开始 | -- | install/uninstall/list 命令 | |

---

## 活跃文件清单

（待 Sprint 启动后填充）

---

## 近期改动记录

| 时间 | 改动目的 | 涉及模块/文件 |
|------|---------|-------------|
| 2026-03-14 | Sprint 1 完成存档，Sprint 2 初始化 | .claude/archive/sprint-1.md |
| 2026-03-14 | 全局 marketplace → hub 重命名 | 全项目 |
| 2026-03-14 | IpHub 设计方案确定 | .claude/research/iphub-design.md |
| 2026-03-14 | Agent CLI 调研完成 | .claude/research/agent-skill-cli-comparison.md |
| 2026-03-14 | 更新所有文档至当前状态 | 全项目文档 |
