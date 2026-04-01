
## 待办事项

### 🔲 [人工] 部署 iphub-bot 修复版到 Cloudflare Workers
- **优先级：** P0（阻塞所有后续功能验证）
- **前置条件：** 无
- **预计耗时：** 10 分钟
- **操作步骤：**
  1. `cd ../iphub-bot`
  2. `git push origin main`（将 4 个新 commit 推送到远程）
  3. `npx wrangler deploy`（部署到 Cloudflare Workers）
  4. `npx wrangler tail`（观察实时日志，等待下一次 cron 触发）
  5. 验证：在日志中看到 `poll_start` + `poll_complete` 事件（不再是 silent failure）
  6. 验证：访问 `https://iphub-bot.<your-domain>.workers.dev/health` 返回 JSON 状态
- **成功标准：** 24 小时内至少 1 个 IP 包 PR 出现在 `twisker/iphub` 仓库

### 🔲 [人工] 确认 Cloudflare Workers 付费计划（Paid Plan）
- **优先级：** P0（影响架构决策）
- **前置条件：** 无
- **预计耗时：** 5 分钟
- **操作步骤：**
  1. 登录 Cloudflare Dashboard → Workers & Pages → 查看当前计划
  2. 如果是 Free Plan：升级到 Workers Paid ($5/月)
     - Free Plan 的 cron 有 10ms CPU 限制，会导致超时
     - Paid Plan 的 cron 无时长限制，是当前架构的前提
  3. 确认后在此处标记完成
- **成功标准：** Dashboard 显示 "Workers Paid" 或 "Workers Bundled"

### 🔲 [人工] 注册 X (Twitter) 开发者账号 + 创建 Bot 应用
- **优先级：** P1（阻塞 X 机器人功能）
- **前置条件：** 部署修复版完成
- **预计耗时：** 30-60 分钟
- **操作步骤：**
  1. 前往 https://developer.twitter.com/en/portal/dashboard
  2. 注册开发者账号（如尚未注册）
  3. 创建新 Project + App，命名为 "IpHub Bot"
  4. 在 App 设置中：
     - User authentication settings → 开启 Read and Write 权限
     - 生成以下凭据：
       - API Key (Consumer Key)
       - API Key Secret (Consumer Secret)
       - Access Token
       - Access Token Secret
       - Bearer Token
  5. 选择 API 定价：
     - 推荐：Pay-as-you-go（按量计费，设置 $30/月上限）
     - 或：Basic Plan ($200/月，如果有预算)
  6. 将凭据写入 Cloudflare Workers Secrets：
     ```bash
     cd ../iphub-bot
     npx wrangler secret put X_BEARER_TOKEN
     npx wrangler secret put X_API_KEY
     npx wrangler secret put X_API_SECRET
     npx wrangler secret put X_ACCESS_TOKEN
     npx wrangler secret put X_ACCESS_SECRET
     ```
  7. 重新部署：`npx wrangler deploy`
  8. 验证：用另一个 X 账号 @mention bot 账号，观察 wrangler tail 日志
- **成功标准：** `wrangler tail` 显示 `poll_start { platform: "x" }` + 成功处理 mention

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

### 🔲 [人工] 创建 X Bot 账号 (@iphub_bot 或类似)
- **优先级：** P1（与 X 开发者注册同步进行）
- **前置条件：** 无
- **预计耗时：** 10 分钟
- **操作步骤：**
  1. 注册新 X 账号，用户名尽量为 `iphub_bot` 或 `iphub_ai`
  2. 完善账号 Profile：
     - 头像：IpHub logo
     - 简介："IpHub Bot — @mention me with an AI skill link, I'll package it for ipman install. Powered by IpMan."
     - 网站：https://twisker.github.io/iphub/
  3. 确认 X 开发者应用绑定到此账号
  4. 更新 `src/handlers/x.ts` 中的 `@iphub_bot` 查询为实际注册的用户名（如果不同）
- **成功标准：** 账号存在且可被 @mention

---

## 已完成事项

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
