# 当前 Sprint

## Sprint 7（Phase 4 — 用户体验改进 + 持续质量保障）— 已完成

**目标：** 简化虚拟环境操作体验，扩展 install 命令支持本地 skill

**状态：** ✅ 全部完成

### A 组：activate/deactivate 脚本改进 ✅

| 任务 | 状态 |
|------|------|
| `ipman init` 命令（bash/zsh/fish/powershell） | ✅ |
| Shell function wrapper 注入/移除/备份 | ✅ |
| `--reverse` 撤销 + `--dry-run` 预览 | ✅ |
| env.py activate/deactivate 消息更新 | ✅ |

### B 组：install 本地 skill 支持 ✅

| 任务 | 状态 |
|------|------|
| `_classify_source()` 三分类（ip_file / local_skill / hub_name） | ✅ |
| `ClaudeCodeAdapter` 本地目录 → copytree | ✅ |
| `OpenClawAdapter` 本地目录 → copytree | ✅ |
| E2E 3 个 skip 测试已解锁 | ✅ |

### 测试统计

- 单元测试：321 passed
- E2E 测试：320 collected（含解锁的 3 个 skill install 测试）
