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
| cli/skill | 技能命令（install/uninstall/list，通过 agent CLI 执行） | -- | `src/ipman/cli/skill.py` | 已完成 |
| cli/pack | IP 包打包命令（pack，合并原 export） | -- | `src/ipman/cli/pack.py` | 已完成 |
| cli/hub | IpHub 命令（search/publish/top） | -- | `src/ipman/cli/hub.py` | 待开始 |

---

## 核心模块索引

| 模块 | 说明 | 设计文档 | 源代码目录 | 状态 |
|------|------|---------|----------|------|
| core/environment | 虚拟环境生命周期管理（创建/激活/删除/切换/状态/prompt tag） | -- | `src/ipman/core/environment.py` | 已完成 |
| core/skill | 技能安装/卸载调度（解析 IpHub 引用 → 调用 agent CLI） | -- | `src/ipman/core/skill.py` | 待开始 |
| core/package | IP 包数据模型 + 解析 + 序列化 | `.claude/research/iphub-design.md` | `src/ipman/core/package.py` | 已完成 |
| core/resolver | 依赖解析引擎（版本匹配 + 递归 + 循环检测） | `.claude/research/iphub-design.md` | `src/ipman/core/resolver.py` | 已完成 |
| core/registry | 本地元数据注册表 | -- | `src/ipman/core/registry.py` | 待开始 |

---

## Agent 适配模块索引

| 模块 | 说明 | 设计文档 | 源代码目录 | 状态 |
|------|------|---------|----------|------|
| agents/base | Agent 适配器基类接口 | -- | `src/ipman/agents/base.py` | 已完成 |
| agents/claude_code | Claude Code 适配（环境探测 + plugin CLI 封装） | `.claude/research/agent-skill-cli-comparison.md` | `src/ipman/agents/claude_code.py` | 已完成（待扩展 skill CLI） |
| agents/registry | Agent 适配器注册与自动探测 | -- | `src/ipman/agents/registry.py` | 已完成 |
| agents/openclaw | OpenClaw 适配（clawhub CLI 封装） | `.claude/research/agent-skill-cli-comparison.md` | `src/ipman/agents/openclaw.py` | 待开始 |

---

## IpHub 模块索引

| 模块 | 说明 | 设计文档 | 源代码目录 | 状态 |
|------|------|---------|----------|------|
| hub/client | IpHub 客户端（index.yaml 拉取/缓存/搜索 + fetch_registry） | `.claude/research/iphub-design.md` | `src/ipman/hub/client.py` | 已完成 |
| hub/publisher | 发布逻辑（fork + 创建注册文件 + 提 PR） | `.claude/research/iphub-design.md` | `src/ipman/hub/publisher.py` | 待开始 |

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
| `tests/test_cli/test_skill.py` | cli/skill | 9 | 已完成 |
| `tests/test_cli/test_pack.py` | cli/pack | 10 | 已完成 |
| `tests/test_cli/test_install_ip.py` | cli/install (IP file) | 8 | 已完成 |
| `tests/test_cli/test_install_hub.py` | cli/install (IpHub) | 7 | 已完成 |
| `tests/test_core/test_package.py` | core/package | 16 | 已完成 |
| `tests/test_core/test_resolver.py` | core/resolver | 19 | 已完成 |
| `tests/test_hub/test_client.py` | hub/client | 12 | 已完成 |
