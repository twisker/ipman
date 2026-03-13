# 模块规格登记表

本文件详细记载各模块的使命。如果事先有详细设计，则指明其设计文档在哪里。如果有源代码或资源文件，则指明其在 repo 中的位置。如果有相关负责人，则指明其身份或联系方式。

---

## 前端模块索引

不适用（IpMan 为纯 CLI 工具，无前端界面）。

---

## CLI 模块索引

| 模块 | 说明 | 设计文档 | 源代码目录 | 状态 |
|------|------|---------|----------|------|
| cli/main | CLI 主入口，Click group 定义 | -- | `src/ipman/cli/main.py` | 已完成 |
| cli/env | 虚拟环境命令（create/activate/deactivate/delete/list/status） | -- | `src/ipman/cli/env.py` | 已完成 |
| cli/skill | 技能命令（install/uninstall/upgrade/list） | -- | `src/ipman/cli/skill.py` | 待开始 |
| cli/pack | IP 包命令（pack/unpack/export） | -- | `src/ipman/cli/pack.py` | 待开始 |
| cli/market | 市场命令（search/publish/top） | -- | `src/ipman/cli/market.py` | 待开始 |

---

## 核心模块索引

| 模块 | 说明 | 设计文档 | 源代码目录 | 状态 |
|------|------|---------|----------|------|
| core/environment | 虚拟环境生命周期管理（创建/激活/删除/切换/状态/prompt tag） | -- | `src/ipman/core/environment.py` | 已完成 |
| core/skill | 技能的安装/卸载/升级/元数据管理 | -- | `src/ipman/core/skill.py` | 待开始 |
| core/package | IP 包的解析/打包/导出 | -- | `src/ipman/core/package.py` | 待开始 |
| core/resolver | 依赖解析引擎 | -- | `src/ipman/core/resolver.py` | 待开始 |
| core/registry | 本地元数据注册表 | -- | `src/ipman/core/registry.py` | 待开始 |

---

## Agent 适配模块索引

| 模块 | 说明 | 设计文档 | 源代码目录 | 状态 |
|------|------|---------|----------|------|
| agents/base | Agent 适配器基类接口 | -- | `src/ipman/agents/base.py` | 已完成 |
| agents/claude_code | Claude Code 技能目录适配 | -- | `src/ipman/agents/claude_code.py` | 已完成 |
| agents/registry | Agent 适配器注册与自动探测 | -- | `src/ipman/agents/registry.py` | 已完成 |
| agents/openclaw | OpenClaw 技能目录适配 | -- | `src/ipman/agents/openclaw.py` | 待开始 |

---

## 市场模块索引

| 模块 | 说明 | 设计文档 | 源代码目录 | 状态 |
|------|------|---------|----------|------|
| market/client | 在线市场 HTTP 客户端 | -- | `src/ipman/market/client.py` | 待开始 |
| market/publisher | 技能/IP 包发布逻辑 | -- | `src/ipman/market/publisher.py` | 待开始 |

---

## 工具模块索引

| 模块 | 说明 | 设计文档 | 源代码目录 | 状态 |
|------|------|---------|----------|------|
| utils/symlink | 跨平台软链接创建/管理 | -- | `src/ipman/utils/symlink.py` | 已完成 |
| utils/i18n | 国际化（中英文自动切换） | -- | `src/ipman/utils/i18n.py` | 待开始 |
| utils/detect | Agent 工具自动探测 | -- | `src/ipman/utils/detect.py` | 待开始 |

---

## 基础设施模块索引

| 模块 | 说明 | 设计文档 | 源代码目录 | 状态 |
|------|------|---------|----------|------|
| CI/CD | GitHub Actions 工作流 | -- | `.github/workflows/` | 已完成 |
| 版本管理脚本 | bump-patch/minor/major | -- | `scripts/` | 已完成 |
| Git Hooks | pre-commit 自动版本递增 | -- | `.githooks/` | 已完成 |

---

## 测试脚本索引

| 测试文件 | 覆盖模块 | 测试数量 | 状态 |
|---------|---------|---------|------|
| `tests/test_core/test_environment.py` | core/environment | 30 | 已完成 |
| `tests/test_core/test_symlink.py` | utils/symlink | 10 | 已完成 |
| `tests/test_cli/test_env.py` | cli/env | 10 | 已完成 |
| `tests/test_cli/test_main.py` | cli/main | 3 | 已完成 |
