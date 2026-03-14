# Sprint 2 存档 — Agent CLI 适配 + IpHub 客户端基础

**日期：** 2026-03-14
**状态：** 已完成（10/10 任务）

---

## 完成的任务

| 任务 | 模块 |
|------|------|
| AgentAdapter 扩展：SkillInfo 数据类 + install/uninstall/list 抽象方法 | agents/base |
| Claude Code 适配器：封装 claude plugin install/uninstall/list CLI | agents/claude_code |
| OpenClaw 适配器：封装 clawhub install/uninstall/list CLI | agents/openclaw |
| `ipman install <name>` 命令（通过 agent CLI 安装） | cli/skill |
| `ipman uninstall <name>` 命令（通过 agent CLI 卸载） | cli/skill |
| `ipman skill list` 命令（通过 agent CLI 列出） | cli/skill |
| IpHub index.yaml 客户端读取与 TTL 缓存 | hub/client |
| `--agent` 参数覆盖自动探测 | cli/skill |
| Agent 适配器 CLI 封装测试（mock subprocess） | tests |
| IpHub 客户端测试 | tests |

## 关键设计决策

1. **subprocess delegation**：所有 skill CRUD 通过 `subprocess.run` 调用 agent 原生 CLI，不接触 agent 内部目录
2. **SkillInfo 数据类**：统一不同 agent 的 skill 信息表示
3. **IpHub 客户端缓存**：基于文件 mtime 的 TTL（1小时），`refresh=True` 绕过
4. **OpenClaw 注册**：支持 `--hub` 自定义源参数

## 测试覆盖

- 新增 37 个测试（16 adapter CLI + 9 CLI skill + 12 hub client）
- 全套 90 个测试全部通过
- ruff + mypy 检查通过
