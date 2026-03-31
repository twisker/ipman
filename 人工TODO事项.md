
## 待办事项

### [AI] CI 集成：E2E 测试自动化
- **What:** 将 E2E 测试集成到 GitHub Actions CI 中
- **Why:** 当前 E2E 测试仅在本地运行（需要 GH_TOKEN、real agents）。CI 没有覆盖集成层，回归只能靠手动发现。
- **Pros:** 每次 PR 自动检测集成回归；真正的 "code + tests green" 门禁。
- **Cons:** 需要 GitHub Actions secrets 配置（GH_TOKEN）；agent-required 测试需要 CI 机器上安装对应工具。
- **Context:** 验证 Sprint 完成后，E2E 测试套件已就位。下一步是让 CI 跑其中可以自动化的部分（mock-based E2E）。真正需要 real agents 的测试用 `@pytest.mark.requires_github_token` 标记，CI 中 skip 或在专用 runner 上运行。
- **Effort:** M (人工: ~1天) → CC+gstack: ~20min
- **Priority:** P2
- **Depends on:** 验证 Sprint 完成

### [人工] 安装 clawhub / OpenClaw CLI
- **What:** 在测试机器上安装 OpenClaw 和 clawhub CLI
- **Why:** Phase 3（OpenClaw 真实集成测试）硬依赖 clawhub。当前机器上不存在，Phase 3 被阻塞。
- **Priority:** P0（Phase 3 前置条件）
- **Action:** 确认 OpenClaw/clawhub 是否公开可安装；如果是，安装并运行 `clawhub --version`。

### [人工] 创建 IpHub 测试 Fork
- **What:** 在 GitHub 上创建 IpHub 测试 Fork（如 `twisker/iphub-test`），预置 3+ 测试条目
- **Why:** Phase 2 E2E 测试需要一个独立的测试 Fork（通过 IPHUB_REPO 环境变量指向），避免污染生产 IpHub
- **Priority:** P0（Phase 2 前置条件）
- **Action:** fork twisker/iphub → 添加测试数据 → 验证 GH_TOKEN 有写权限
