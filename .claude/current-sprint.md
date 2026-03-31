# 当前 Sprint：综合验证 Sprint（Comprehensive Validation Sprint）

**目标：** 在社区发布前，通过真实 agent 测试证明 IpMan 的每个功能设计目标均已实现。
**设计文档：** `~/.gstack/projects/twisker-ipman/twister-dev-design-20260331-190046.md`
**分支：** `dev`
**开始日期：** 2026-03-31
**预计完成：** 2026-04-13（2-3周含缓冲）

## 阶段进度

| 阶段 | 内容 | 状态 | 备注 |
|------|------|------|------|
| Phase 0 | 环境建立 + 基线修复 | ✅ 已完成（commit 00e9c3a） | mypy 0 errors, ruff clean |
| Phase 1 | 规格审计 + 需求矩阵提取 | ✅ 已完成 | 36 需求行，10 个覆盖缺口已识别 |
| Phase 2 | IpHub 验证（测试 fork） | ✅ 已完成 | 17/17 E2E 通过；fork 已 seed；CI job 已添加 |
| Phase 3 | OpenClaw 真实集成 | 🔄 进行中 | CI 通过 npm 自动安装；本地跳过；test_openclaw_real.py 已就位 |
| Phase 4 | 核心模块验证 + 性能基准 | ⏳ 待开始 | |
| Phase 5 | 合规报告 | ⏳ 待开始 | |

## Phase 0 完成内容（已提交）

| 修复 | 文件 |
|------|------|
| urlopen timeout=30 + URLError/YAMLError 处理 | hub/client.py |
| yaml.safe_load None 守卫 → HubError | hub/client.py |
| IPHUB_REPO env var 覆盖（生产 repo 保护） | hub/publisher.py, hub/stats.py |
| is_installed() 检查 clawhub 而非 openclaw | agents/openclaw.py |
| **kwargs: str \| bool \| None 类型修复 | agents/base.py, claude_code.py |
| 7 个 mypy --strict 注解修复 | passthrough.py, _common.py, environment.py |
| IPHUB_TEST_REPO → IPHUB_REPO 统一 | tests/e2e/conftest.py |
| 新增 URLError + empty YAML 测试 | tests/test_hub/test_client.py |
| 新建 test_openclaw_real.py（requires_clawhub marker） | tests/e2e/ |
| resolver.resolve_dependencies() 接入 CLI | cli/skill.py |
| requires_clawhub 测试标记注册 | pyproject.toml |

## Phase 1 活跃任务

| # | 任务 | 状态 |
|---|------|------|
| 1.1 | 读取 arch-spec-registry.md | ✅ 完成 |
| 1.2 | 读取 module-spec-registry.md + 更新过时状态 | ✅ 完成 |
| 1.3 | 读取 tech-spec-registry.md | ✅ 完成 |
| 1.4 | 读取 validation-registry.md | ✅ 完成 |
| 1.5 | 读取 test-registry.md | ✅ 完成 |
| 1.6 | 读取 research/iphub-design.md | ✅ 完成 |
| 1.7 | 读取 research/agent-skill-cli-comparison.md | ✅ 完成 |
| 1.8 | 提取需求矩阵（每条设计目标 → 需求行） | ✅ 完成（见下方） |
| 1.9 | 识别测试覆盖缺口 | ✅ 完成（见下方） |

---

## Phase 1 输出：需求矩阵

> 每条设计目标对应一行。来源：arch/module/tech/validation spec + iphub-design + agent-skill-cli-comparison。

| # | 需求 | 来源 | 单测 | E2E | 状态 |
|---|------|------|------|-----|------|
| REQ-A01 | 所有 skill CRUD 通过 agent CLI，不侵入 agent 内部目录 | arch, validation | test_adapters_cli.py | Phase 3 | ✅ |
| REQ-A02 | 插件式适配：新增 agent 不影响核心逻辑 | arch | test_adapters_cli.py | -- | ✅ |
| REQ-A03 | 跨平台：pathlib，Windows 软链接降级 | arch, tech | test_symlink.py | CI matrix | 部分（CI 矩阵未覆盖 Windows） |
| REQ-A04 | CLI 冷启动 < 500ms | tech, validation | -- | benchmark | ⚠️ 无性能测试 |
| REQ-A05 | 单技能安装 < 5s（本地），< 15s（网络） | tech, validation | -- | benchmark | ⚠️ 无性能测试 |
| REQ-A06 | 50 个依赖解析 < 3s | validation | test_resolver.py（无时间断言） | benchmark | ⚠️ 无性能断言 |
| REQ-A07 | mypy strict + ruff clean + 100% 测试通过 | validation | CI | -- | ✅ |
| REQ-AG01 | 自动探测已安装 agent 工具及版本 | validation | test_adapters_cli.py | -- | ✅ |
| REQ-AG02 | 根据项目目录猜测所用 agent | validation | -- | -- | ⚠️ 未覆盖 |
| REQ-AG03 | --agent 参数覆盖自动探测 | validation | test_skill.py | -- | ✅ |
| REQ-AG04 | 适配器不侵入 agent 内部目录 | validation | test_adapters_cli.py | -- | ✅ |
| REQ-SK01 | ipman install 调用 agent 原生 CLI | validation | test_install_hub.py, test_install_ip.py | Phase 3 | ✅ |
| REQ-SK02 | ipman uninstall 调用 agent 原生 CLI | validation | test_skill.py | Phase 3 | ✅ |
| REQ-SK03 | ipman skill list 调用 agent 原生 CLI | validation | test_skill.py | Phase 3 | ✅ |
| REQ-IP01 | IP 文件符合 YAML schema | iphub-design | test_package.py | -- | ✅ |
| REQ-IP02 | 自动生成 IP 文件头部包含 IpMan 引用 | iphub-design | test_pack.py | -- | ✅ |
| REQ-IP03 | 递归依赖解析 | iphub-design | test_resolver.py | -- | ✅ |
| REQ-IP04 | 循环依赖检测并报错 | iphub-design | test_resolver.py | -- | ✅ |
| REQ-HUB01 | 拉取并缓存 index.yaml，URLError/空 YAML 报 HubError | iphub-design | test_client.py | Phase 2 | ✅ |
| REQ-HUB02 | 搜索基于本地 index.yaml 过滤 | iphub-design | test_client.py, test_hub.py | Phase 2 | ✅ |
| REQ-HUB03 | 安装：解析引用 → 调用 agent CLI → 计数 | iphub-design | test_install_hub.py | Phase 2 | ✅（计数部分未有单测） |
| REQ-HUB04 | 发布：fork → 创建注册文件 → 提 PR | iphub-design | test_publisher.py | Phase 2 | ✅ |
| REQ-HUB05 | 认证基于 GitHub PR author（gh CLI） | iphub-design | test_publisher.py | Phase 2 | ✅ |
| REQ-HUB06 | 安装计数：issue comment + reaction | iphub-design | test_stats.py | Phase 2 | ✅ |
| REQ-HUB07 | IpHub 只存引用，不存 skill 内容 | iphub-design | -- | 架构约束 | ✅（设计满足） |
| REQ-ENV01 | create 在 project/user/machine 三 scope 下正确创建 | validation | test_environment.py | -- | ✅ |
| REQ-ENV02 | activate 后 shell prompt tag 注入 | validation, tech | test_environment.py, test_shell_init.py | -- | ✅ |
| REQ-ENV03 | deactivate 恢复原始提示符 | validation | test_environment.py | -- | ✅ |
| REQ-ENV04 | delete 清理所有软链接和环境文件 | validation | test_environment.py | -- | ✅ |
| REQ-ENV05 | 多环境并存互不干扰 | validation | test_environment.py | -- | ✅ |
| REQ-SEC01 | 软链接路径穿越防护 | tech | test_symlink_guard.py | -- | ✅ |
| REQ-SEC02 | 风险评估引擎（vetter）+ 安全决策矩阵 | -- | test_vetter.py, test_security.py | test_security_flow.py | ✅ |
| REQ-SEC03 | 安全模式（permissive/default/cautious/strict） | -- | test_install_security.py | test_security_flow.py | ✅ |
| REQ-I18N01 | LANG=zh* 时自动切换中文 | validation | test_i18n.py | -- | ✅ |
| REQ-TECH01 | Python 3.10+ | tech | CI | -- | ✅ |
| REQ-TECH02 | PyPI 可安装（pip install ipman） | tech, validation | -- | TestPyPI | ⚠️ 未验证 |

---

## Phase 1 输出：测试覆盖缺口

| 缺口 | 类型 | 优先级 | 对应需求 |
|------|------|--------|---------|
| 无性能基准测试（启动时间、安装时间、解析时间） | 性能 | 中 | REQ-A04, REQ-A05, REQ-A06 |
| 无 agent 自动探测测试（根据项目目录猜测） | 功能 | 中 | REQ-AG02 |
| 无安装计数单测（hub/stats 仅 4 tests，未测 E2E 路径） | 功能 | 低 | REQ-HUB03 |
| core/skill.py 缺失（模块未实现） | 模块 | 高 | REQ-SK01~03 |
| core/registry.py 缺失（模块未实现） | 模块 | 高 | -- |
| utils/detect.py 缺失（模块未实现） | 模块 | 中 | REQ-AG01~02 |
| Windows CI 矩阵未覆盖软链接测试 | 平台 | 中 | REQ-A03 |
| PyPI 发布验证（TestPyPI 未跑） | 发布 | 低 | REQ-TECH02 |
| E2E IpHub 验证（需 iphub-test fork） | E2E | 高 | REQ-HUB01~06（Phase 2） |
| E2E OpenClaw 真实集成（需 clawhub） | E2E | 高 | REQ-SK01~03, REQ-AG01（Phase 3） |

## 改动记录

| 日期 | 提交 | 内容 |
|------|------|------|
| 2026-03-31 | b624944 | 添加 CEO 审查 TODO 事项 |
| 2026-03-31 | 00e9c3a | Phase 0 全部修复（mypy+架构+测试） |
