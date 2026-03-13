# 当前 Sprint

**Sprint 0 - 项目初始化**

**目标：** 建立开发框架，搭建 Python 项目骨架、CI/CD 流水线、测试框架

---

## 任务列表

| 优先级 | 任务 | 所属模块 | 责任人 | 状态 |
|-------|------|----------|--------|------|
| P0 | 初始化 pyproject.toml（uv 项目配置） | 基础设施 | AI | 已完成 |
| P0 | 创建 src/ipman 包目录结构 | 基础设施 | AI | 已完成 |
| P0 | 配置 ruff（lint + 格式化） | 基础设施 | AI | 已完成 |
| P0 | 配置 mypy（类型检查） | 基础设施 | AI | 已完成 |
| P0 | 配置 pytest（测试框架） | 测试 | AI | 已完成 |
| P1 | 实现 Click CLI 主入口（`ipman --help`） | CLI | AI | 已完成 |
| P1 | 搭建 GitHub Actions CI（三平台测试矩阵） | CI/CD | AI | 已完成 |
| P1 | 创建 GitHub 仓库描述和标签 | 基础设施 | 人工 | 已完成 |

---

## 模块状态

| 模块 | 状态 | 最后更新 | 当前目标 | 备注 |
|------|------|---------|---------|------|
| 基础设施 | 稳定 | 2026-03-13 | -- | pyproject.toml + 目录结构 + 版本管理 完成 |
| CLI | 稳定 | 2026-03-13 | -- | Click 主入口 + info 命令 完成 |
| 测试 | 稳定 | 2026-03-13 | -- | pytest 配置 + 3 个 CLI 测试通过 |
| CI/CD | 稳定 | 2026-03-13 | -- | GitHub Actions 三平台矩阵配置完成 |

---

## 活跃文件清单

无（所有 AI 任务已完成）

---

## 近期改动记录

| 时间 | 改动目的 | 涉及模块/文件 |
|------|---------|-------------|
| 2026-03-13 | Sprint 0 启动 | .claude/current-sprint.md |
| 2026-03-13 | 项目骨架搭建 | pyproject.toml, src/ipman/**, tests/** |
| 2026-03-13 | CLI 主入口实现 | src/ipman/cli/main.py, tests/test_cli/test_main.py |
| 2026-03-13 | CI 配置 | .github/workflows/ci.yml |
| 2026-03-13 | README banner + slogan | README.md, images/IpMan.jpg |

---

## Sprint 0 总结

所有 AI 任务已完成。剩余 1 项人工任务（H01: 创建 GitHub 仓库描述和标签）。

验证结果：
- pytest: 3/3 通过
- ruff: 无问题
- mypy: strict 模式无问题
- `ipman --help`: 正常输出
