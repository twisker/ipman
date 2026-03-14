# Sprint 5 存档

**Sprint 5 - 代码质量 + 发布准备**

**目标：** 代码去重、质量检查、文档完善、PyPI 发布准备

**状态：** 已完成

**完成日期：** 2026-03-14

---

## 任务列表

| 优先级 | 任务 | 状态 |
|-------|------|------|
| P0 | `_resolve_agent` 去重提取到 `cli/_common.py` | 已完成 |
| P0 | pyproject.toml 动态版本（VERSION → hatchling） | 已完成 |
| P1 | ruff + mypy 全量检查通过 | 已完成 |
| P1 | README.md 更新（CLI 参考 + Roadmap） | 已完成 |
| P2 | GitHub Actions 发布工作流（tag → PyPI） | 已完成 |

---

## 关键改动

1. **版本统一**：VERSION 文件 → hatchling 动态注入 → importlib.metadata 读取
2. **代码去重**：`_resolve_agent` 从 skill.py/pack.py 提取到 `cli/_common.py`
3. **质量门禁**：ruff 0 errors, mypy 0 errors, 176 tests 全通过
4. **发布管道**：`v*` tag push 触发 OIDC trusted publisher 发布到 PyPI
