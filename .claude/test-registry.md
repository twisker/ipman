# 测试登记表

本文件记载各模块的测试覆盖情况（包括覆盖率要求、当前覆盖率、当前状态等）、测试规范、测试场景（包括目标模块、测试描述、测试文件等）。

---

## 通用测试规范

| 规范 | 要求 |
|------|------|
| 单元测试覆盖率 | 核心业务逻辑 >= 80% |
| CLI 测试 | 所有 Click 命令必须有 CliRunner 集成测试 |
| 跨平台测试 | CI 矩阵覆盖 Linux、macOS、Windows |
| 软链接测试 | 需在三平台验证软链接创建/删除行为 |
| TDD | 先写测试，再写实现 |

---

## 核心模块测试覆盖

| 模块 | 测试文件 | 覆盖率要求 | 当前覆盖率 | 状态 |
|------|---------|-----------|-----------|------|
| core/environment | `tests/test_core/test_environment.py` | >= 80% | 30 tests passed | 已完成 |
| core/skill | `tests/test_core/test_skill.py` | >= 80% | -- | 待开始 |
| core/package | `tests/test_core/test_package.py` | >= 80% | 16 tests passed | 已完成 |
| core/resolver | `tests/test_core/test_resolver.py` | >= 80% | 19 tests passed | 已完成 |
| core/registry | `tests/test_core/test_registry.py` | >= 80% | -- | 待开始 |

---

## CLI 测试覆盖

| 模块 | 测试文件 | 覆盖率要求 | 当前覆盖率 | 状态 |
|------|---------|-----------|-----------|------|
| cli/env | `tests/test_cli/test_env.py` | >= 70% | 10 tests passed | 已完成 |
| cli/skill | `tests/test_cli/test_skill.py` | >= 70% | 9 tests passed | 已完成 |
| cli/pack | `tests/test_cli/test_pack.py` | >= 70% | 10 tests passed | 已完成 |
| cli/install (IP) | `tests/test_cli/test_install_ip.py` | >= 70% | 8 tests passed | 已完成 |
| cli/install (Hub) | `tests/test_cli/test_install_hub.py` | >= 70% | 7 tests passed | 已完成 |
| cli/hub | `tests/test_cli/test_hub.py` | >= 70% | 12 tests passed | 已完成 |

---

## Agent 适配测试覆盖

| 模块 | 测试文件 | 覆盖率要求 | 当前覆盖率 | 状态 |
|------|---------|-----------|-----------|------|
| agents/claude_code | `tests/test_agents/test_claude_code.py` | >= 80% | -- | 待开始 |
| agents/openclaw | `tests/test_agents/test_openclaw.py` | >= 80% | -- | 待开始 |
| utils/detect | `tests/test_core/test_detect.py` | >= 80% | -- | 待开始 |

---

## 工具模块测试覆盖

| 模块 | 测试文件 | 覆盖率要求 | 当前覆盖率 | 状态 |
|------|---------|-----------|-----------|------|
| utils/symlink | `tests/test_core/test_symlink.py` | >= 90% | 10 tests passed | 已完成 |
| utils/i18n | `tests/test_core/test_i18n.py` | >= 70% | -- | 待开始 |

---

## 基础设施与部署测试覆盖

| 模块 | 测试文件 | 覆盖要求 | 状态 |
|------|---------|---------|------|
| CI/CD 流水线 | -- | 三平台全流程冒烟测试 | 待开始 |
| PyPI 发布 | -- | TestPyPI 发布验证 | 待开始 |

---

## 测试场景登记

> 待各 Sprint 开发启动后，逐步填充具体测试场景。

| Sprint | 目标模块 | 测试描述 | 测试文件 | 结果 |
|--------|---------|---------|---------|------|
| Sprint 1 | core/environment | 虚拟环境 CRUD、scope、prompt tag、状态管理 | `tests/test_core/test_environment.py` | 30/30 通过 |
| Sprint 1 | utils/symlink | 跨平台软链接创建/删除/验证 | `tests/test_core/test_symlink.py` | 10/10 通过 |
| Sprint 1 | cli/env | CLI env 子命令集成测试（CliRunner） | `tests/test_cli/test_env.py` | 10/10 通过 |
| Sprint 1 | cli/main | CLI 主入口帮助/版本 | `tests/test_cli/test_main.py` | 3/3 通过 |
| Sprint 2 | agents/claude_code | Claude Code 适配器 skill CLI 封装 | `tests/test_agents/test_claude_code.py` | 10/10 通过 |
| Sprint 2 | agents/openclaw | OpenClaw 适配器 CLI 封装 | `tests/test_agents/test_openclaw.py` | 10/10 通过 |
| Sprint 2 | cli/skill | install/uninstall/list 命令 | `tests/test_cli/test_skill.py` | 9/9 通过 |
| Sprint 2 | hub/client | IpHub index 拉取/缓存/搜索/lookup | `tests/test_hub/test_client.py` | 12/12 通过 |
| Sprint 3 | core/package | IP 包数据模型 + 解析 + 序列化 | `tests/test_core/test_package.py` | 16/16 通过 |
| Sprint 3 | core/resolver | 版本匹配 + 递归解析 + 循环检测 | `tests/test_core/test_resolver.py` | 19/19 通过 |
| Sprint 3 | cli/pack | pack 命令 | `tests/test_cli/test_pack.py` | 10/10 通过 |
| Sprint 3 | cli/install (IP) | .ip.yaml 本地文件安装 | `tests/test_cli/test_install_ip.py` | 8/8 通过 |
| Sprint 3 | cli/install (Hub) | IpHub 短名称安装 + fetch_registry | `tests/test_cli/test_install_hub.py` | 7/7 通过 |
| Sprint 4 | cli/hub | search/info/top/publish CLI 命令 | `tests/test_cli/test_hub.py` | 12/12 通过 |
| Sprint 4 | hub/publisher | 发布引擎 (fork/push/PR) | `tests/test_hub/test_publisher.py` | 10/10 通过 |
| Sprint 4 | hub/stats | 安装统计上报 | `tests/test_hub/test_stats.py` | 4/4 通过 |
