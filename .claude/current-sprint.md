# 当前 Sprint

**Sprint 2 - Agent CLI 适配 + IpHub 客户端基础**

**目标：** 基于 agent CLI 命令封装技能安装/卸载；实现 IpHub 引用注册表的客户端读取

**状态：** 进行中

---

## 前置条件

- [x] Sprint 1 已完成并存档
- [x] Agent CLI 调研完成（`.claude/research/agent-skill-cli-comparison.md`）
- [x] IpHub 设计方案确定（`.claude/research/iphub-design.md`）
- [x] 人工确认开始 Sprint 2

---

## 任务列表

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

## 模块状态

| 模块 | 状态 | 最后更新 | 当前目标 | 备注 |
|------|------|---------|---------|------|
| agents/base | 已完成 | 2026-03-14 | -- | 添加 SkillInfo + install/uninstall/list 抽象方法 |
| agents/claude_code | 已完成 | 2026-03-14 | -- | 封装 claude plugin CLI（subprocess） |
| agents/openclaw | 已完成 | 2026-03-14 | -- | 封装 clawhub CLI（subprocess） |
| agents/registry | 已完成 | 2026-03-14 | -- | 注册 OpenClaw 适配器 |
| hub/client | 已完成 | 2026-03-14 | -- | index.yaml 拉取 + TTL 缓存 + search/lookup |
| cli/skill | 已完成 | 2026-03-14 | -- | install/uninstall/list + --agent 参数 |

---

## 活跃文件清单

- `src/ipman/agents/base.py`
- `src/ipman/agents/claude_code.py`
- `src/ipman/agents/openclaw.py`
- `src/ipman/agents/registry.py`
- `src/ipman/cli/skill.py`
- `src/ipman/cli/main.py`
- `src/ipman/hub/client.py`
- `tests/test_agents/test_adapters_cli.py`
- `tests/test_cli/test_skill.py`
- `tests/test_hub/test_client.py`

---

## 近期改动记录

| 时间 | 改动目的 | 涉及模块/文件 |
|------|---------|-------------|
| 2026-03-14 | Sprint 2 启动 | .claude/current-sprint.md |
| 2026-03-14 | 扩展 AgentAdapter：SkillInfo + install/uninstall/list 抽象方法 | agents/base |
| 2026-03-14 | Claude Code 适配器：封装 claude plugin CLI（subprocess） | agents/claude_code |
| 2026-03-14 | 新建 OpenClaw 适配器：封装 clawhub CLI（subprocess） | agents/openclaw |
| 2026-03-14 | 注册 OpenClaw 到适配器注册表 | agents/registry |
| 2026-03-14 | 实现 CLI skill 命令：install/uninstall/skill list + --agent | cli/skill, cli/main |
| 2026-03-14 | 实现 IpHub 客户端：fetch_index + TTL 缓存 + search + lookup | hub/client |
| 2026-03-14 | 编写 37 个新测试（全部通过，总计 90） | tests/ |
