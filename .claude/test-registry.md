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
| core/environment | `tests/test_core/test_environment.py` | >= 80% | -- | 待开始 |
| core/skill | `tests/test_core/test_skill.py` | >= 80% | -- | 待开始 |
| core/package | `tests/test_core/test_package.py` | >= 80% | -- | 待开始 |
| core/resolver | `tests/test_core/test_resolver.py` | >= 80% | -- | 待开始 |
| core/registry | `tests/test_core/test_registry.py` | >= 80% | -- | 待开始 |

---

## CLI 测试覆盖

| 模块 | 测试文件 | 覆盖率要求 | 当前覆盖率 | 状态 |
|------|---------|-----------|-----------|------|
| cli/env | `tests/test_cli/test_env.py` | >= 70% | -- | 待开始 |
| cli/skill | `tests/test_cli/test_skill.py` | >= 70% | -- | 待开始 |
| cli/pack | `tests/test_cli/test_pack.py` | >= 70% | -- | 待开始 |
| cli/market | `tests/test_cli/test_market.py` | >= 70% | -- | 待开始 |

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
| utils/symlink | `tests/test_core/test_symlink.py` | >= 90% | -- | 待开始 |
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
| | | | | |
