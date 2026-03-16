# 当前 Sprint

## Sprint 7（Phase 4 — 用户体验改进 + 持续质量保障）

**目标：** 简化虚拟环境操作体验，扩展 install 命令支持本地 skill

**状态：** 进行中（A 组已完成，B 组待开始）

### A 组：activate/deactivate 脚本改进 ✅ 已完成

| 任务 | 状态 |
|------|------|
| `ipman init` 命令（bash/zsh/fish/powershell） | ✅ 已完成 |
| Shell function wrapper 注入/移除/备份 | ✅ 已完成 |
| `--reverse` 撤销 + `--dry-run` 预览 | ✅ 已完成 |
| env.py activate/deactivate 消息更新 | ✅ 已完成 |

### B 组：install 本地 skill 支持 — 待开始

| 优先级 | 任务 | 状态 |
|--------|------|------|
| P0 | 扩展 `ipman install` 支持本地 skill 目录/文件（自动检测类型） | 待设计 |
| P0 | 更新 E2E fixture 为正确 plugin 结构，解锁 3 个 skip 测试 | 待开始 |
| P1 | `ClaudeCodeAdapter.install_skill()` 区分远程名称 vs 本地路径 | 待开始 |
| P1 | `OpenClawAdapter.install_skill()` 本地路径走文件复制 | 待开始 |

### 活跃文件

- `src/ipman/core/shell_init.py` — 新建（A 组）
- `src/ipman/cli/init.py` — 新建（A 组）
- `src/ipman/agents/claude_code.py` — 待修改（B 组）
- `src/ipman/agents/openclaw.py` — 待修改（B 组）
- `src/ipman/cli/skill.py` — 待修改（B 组）
- `tests/e2e/test_skill_install.py` — 待修改（B 组）
