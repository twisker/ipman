
## 待办事项

### 🔲 [人工] 注册微博开发者账号（Weibo Developer Certification）
- **优先级：** P2（阻塞微博机器人，但不阻塞其他功能）
- **前置条件：** 无
- **预计耗时：** 1-2 周（审核周期）
- **操作步骤：**
  1. 前往 https://open.weibo.com/
  2. 使用微博账号登录
  3. 申请成为开发者（需要实名认证）
  4. 创建新应用，选择"网页应用"类型
  5. 填写应用信息：
     - 应用名称：IpHub Bot
     - 应用描述：AI 技能包自动发现与管理机器人
     - 回调地址：`https://iphub-bot.<your-domain>.workers.dev/webhook/weibo`
  6. 等待审核通过
  7. 审核通过后获取 App Key 和 Access Token
  8. 将凭据写入 Cloudflare Workers Secrets：
     ```bash
     cd ../iphub-bot
     npx wrangler secret put WEIBO_APP_KEY
     npx wrangler secret put WEIBO_ACCESS_TOKEN
     ```
- **成功标准：** 微博开放平台显示应用状态为"已审核"

---

## 已完成事项

### ✅ [人工] 确认 Cloudflare Workers 付费计划（Paid Plan）
- **完成日期：** 2026-04-03
- **结果：** 已升级到 Workers Paid 计划，cron 无时长限制

### ✅ [人工] 部署 iphub-bot 修复版到 Cloudflare Workers
- **完成日期：** 2026-04-03
- **结果：** feature/unified-platform → dev → main 合并完成，已部署到 Cloudflare Workers

### ✅ [人工] 创建 X Bot 账号 + 注册 X 开发者应用
- **完成日期：** 2026-04-03
- **结果：** 
  - 使用 `@iphub_bot` 账号在 developer.x.com 开通开发者权限并创建 App
  - 头像已设置（pixel art 风格 IpHub Bot icon）
  - X API 凭据（Bearer Token / OAuth 1.0 Consumer Key & Secret / Access Token & Secret）已配置到 Cloudflare Workers Secrets
  - 凭据映射：Bearer Token → `X_BEARER_TOKEN`，Consumer Key → `X_API_KEY`，Consumer Secret → `X_API_SECRET`，Access Token → `X_ACCESS_TOKEN`，Access Token Secret → `X_ACCESS_SECRET`

### ✅ [人工] 创建 IpHub 测试 Fork
- **完成日期：** 2026-03-31
- **结果：** `twisker/iphub-test` 已创建并由 AI 自动 seed（index.yaml + 2 skill + 1 package 注册文件）
- **影响：** Phase 2 E2E 测试 17/17 通过；`IPHUB_REPO=twisker/iphub-test` 已设置为 GitHub Actions 变量

### ✅ [AI] CI 集成：E2E 测试自动化
- **完成日期：** 2026-03-31
- **结果：**
  - `e2e-fast.yml`：每次 push 运行 Layer 1 平台测试（三平台矩阵）
  - `e2e-full.yml`：每日定时 + tag，包含：
    - `e2e-agents` job：claude-code + openclaw 矩阵（npm 自动安装 agent CLI）
    - `e2e-hub-integration` job：Phase 2 IpHub 网络集成测试（IPHUB_REPO 变量已配置）
    - `e2e-publish-security` job：发布安全测试（需 GH_TOKEN_OWNER secret）
  - Phase 3 OpenClaw：`npm install -g openclaw` 在 CI 中自动安装；`test_openclaw_real.py` 已就位

### ✅ [人工] 安装 clawhub / OpenClaw CLI（本地机器）
- **完成日期：** 2026-03-31（等效）
- **结果：** 本地不需要手动安装。CI 通过 `npm install -g openclaw` 自动处理；本地运行时 `requires_clawhub` 测试自动跳过（clawhub 不在 PATH）
- **影响：** Phase 3 测试将在下次 e2e-full CI 触发时自动运行
