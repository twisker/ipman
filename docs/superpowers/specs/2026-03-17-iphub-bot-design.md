# IpHub Bot — Social Media Auto IP Generation Design Spec

> IpMan - Intelligence Package Manager
> Date: 2026-03-17
> Status: Approved
> Sprint: 13 (Phase 5 — Sub-4)

## 1. Background & Motivation

To make IpHub go viral, users should be able to @mention an iphub bot on X or Weibo when they see interesting agent tools/skills. The bot analyzes the post with AI, auto-generates an IP package, and submits a PR to iphub — turning any social media post into an installable skill kit.

Additionally, the bot periodically polls free developer data sources (GitHub Trending, Hacker News, Reddit, Product Hunt, Dev.to) to discover new agent-related tools and auto-create IP packages.

## 2. Architecture

```
User @mentions iphub bot on X/Weibo
        ↓
X/Weibo Webhook → Cloudflare Worker (entry point)
        ↓
AI Analysis (Claude API → fallback Cloudflare Workers AI)
        ↓
Generate ip.yaml → Submit PR to iphub via GitHub API
        ↓
Bot replies: "IP created! ipman install xxx"
```

## 3. Cloudflare Worker Routes

| Route | Function |
|-------|----------|
| `POST /webhook/x` | Receive X @mention webhook |
| `POST /webhook/weibo` | Receive Weibo @mention webhook |
| `POST /poll/github-trending` | Cron-triggered GitHub Trending scan |
| `POST /poll/hackernews` | Cron-triggered HN scan |
| `POST /poll/reddit` | Cron-triggered Reddit scan |
| `POST /poll/producthunt` | Cron-triggered Product Hunt scan |
| `POST /poll/devto` | Cron-triggered Dev.to scan |
| `GET /health` | Health check |

## 4. Core Processing Pipeline

Shared across all data sources:

1. **Receive** — Extract content text, author, URL from webhook/poll payload
2. **Analyze** — Call AI to determine relevance and extract skill/tool info
3. **Filter** — If AI says "not relevant", ignore silently
4. **Deduplicate** — Check if an IP with similar name/URL already exists in iphub index
5. **Generate** — Create ip.yaml content from AI output
6. **Submit** — Create PR to iphub via GitHub API (fork → branch → push file → PR)
7. **Reply** — Post reply on original platform with install command (webhook sources only)

## 5. AI Analysis

### 5.1 Model selection with fallback

```typescript
async function analyze(content: string): Promise<AnalysisResult> {
    try {
        return await analyzeWithClaude(content);
    } catch (e) {
        // Claude API failure (rate limit, balance, etc.)
        return await analyzeWithCFAI(content);
    }
}
```

### 5.2 Prompt

```
You are the IpHub bot. Analyze the following content and determine if it describes
AI agent skills, tools, or plugins that could be packaged as an IpMan IP.

Content: {text}
URL: {url}
Author: {author}
Source: {platform}

If relevant, output JSON:
{
  "relevant": true,
  "ip_name": "lowercase-hyphenated-name",
  "description": "One-line description",
  "tags": ["tag1", "tag2"],
  "skills": [{"name": "skill-name", "description": "what it does"}],
  "summary": "2-3 sentences explaining the value of this IP package",
  "source_url": "{url}",
  "source_author": "{author}"
}

If not relevant to AI agents/skills, output: {"relevant": false}
```

### 5.3 Analysis result validation

- `ip_name` must match `^[a-z0-9][a-z0-9\-]{1,48}[a-z0-9]$`
- `tags` must each match `^[a-z0-9][a-z0-9\-]{0,28}[a-z0-9]$`, max 10
- `skills` must have at least 1 entry
- If validation fails, discard the result

## 6. GitHub PR Submission

Uses GitHub REST API (not `gh` CLI, since we're in a Cloudflare Worker):

1. Fork iphub repo (if bot account doesn't already have a fork)
2. Create branch: `bot/auto-{ip_name}-{timestamp}`
3. Create/update files:
   - `registry/@iphub-bot/{ip_name}/meta.yaml`
   - `registry/@iphub-bot/{ip_name}/1.0.0.yaml`
4. Create PR with body explaining the source (tweet URL, HN link, etc.)

Bot-generated IPs go under the `@iphub-bot` namespace to distinguish from user-published IPs.

## 7. Rate Limiting & Anti-Abuse

| Protection | Mechanism |
|-----------|-----------|
| Per-user rate limit | Max 5 @mentions per user per hour (stored in Cloudflare KV) |
| Global rate limit | Max 50 PRs per day |
| Duplicate detection | Check iphub index before generating |
| Content filter | AI prompt includes instruction to reject spam/inappropriate content |

## 8. Worker Secrets

| Secret | Purpose |
|--------|---------|
| `ANTHROPIC_API_KEY` | Claude API for analysis |
| `CF_AI_BINDING` | Cloudflare Workers AI (fallback) |
| `X_BEARER_TOKEN` | X API read/reply |
| `WEIBO_ACCESS_TOKEN` | Weibo API read/reply |
| `GITHUB_TOKEN` | Submit PRs to iphub (bot account PAT) |
| `IPHUB_INDEX_URL` | URL to fetch iphub index.yaml for dedup |

## 9. Batch Delivery Plan

| Batch | Content | Dependencies |
|-------|---------|-------------|
| **Batch 1** | Worker skeleton + AI analysis + GitHub PR submission + dedup | Cloudflare account, GitHub bot account |
| **Batch 2** | X (Twitter) webhook integration | Batch 1 + X API developer account ($100/month Basic for mentions) |
| **Batch 3** | Weibo webhook integration | Batch 1 + Weibo open platform developer certification |
| **Batch 4** | Free data source polling: GitHub Trending | Batch 1 |
| **Batch 5** | Free data source polling: Hacker News + Reddit + Product Hunt + Dev.to | Batch 1 |

Batch 1 is the core — once built, Batches 2-5 are data source adapters.

Note: X Basic API ($100/month) is needed for reading @mentions. This is a recurring cost. Weibo requires developer certification (free but bureaucratic). Free data sources (Batch 4-5) have no cost.

## 10. Repository Structure

New repository: `twisker/iphub-bot`

```
iphub-bot/
  src/
    index.ts                # Worker entry + router
    handlers/
      x.ts                  # X webhook handler
      weibo.ts              # Weibo webhook handler
      github-trending.ts    # GitHub Trending poller
      hackernews.ts         # HN poller
      reddit.ts             # Reddit poller
      producthunt.ts        # Product Hunt poller
      devto.ts              # Dev.to poller
    services/
      ai-analyzer.ts        # AI analysis (Claude → CF AI fallback)
      ip-generator.ts       # Generate ip.yaml content
      github-pr.ts          # Submit PR to iphub via API
      dedup.ts              # Check for duplicate IPs
      reply.ts              # Reply on source platform
    utils/
      rate-limiter.ts       # KV-based rate limiting
      validator.ts          # Validate AI output (name, tags format)
  wrangler.toml             # Cloudflare Worker config
  package.json
  tsconfig.json
  README.md
```

## 11. Cron Triggers (wrangler.toml)

```toml
[triggers]
crons = [
  "0 */6 * * *",   # Every 6 hours: GitHub Trending
  "0 */4 * * *",   # Every 4 hours: Hacker News
  "0 */8 * * *",   # Every 8 hours: Reddit
  "0 12 * * *",    # Daily: Product Hunt
  "0 18 * * *",    # Daily: Dev.to
]
```

## 12. Impact on Existing Repos

| Repo | Changes |
|------|---------|
| `twisker/iphub-bot` | **New repo** — all bot code |
| `twisker/iphub` | No code changes — bot submits PRs through existing validate-pr workflow |
| `twisker/ipman` | No changes |

## 13. Human Prerequisites

- [ ] Create Cloudflare account (free tier)
- [ ] Create GitHub bot account (e.g. `iphub-bot`) with PAT
- [ ] (Batch 2) Apply for X API Basic tier ($100/month)
- [ ] (Batch 3) Apply for Weibo open platform developer certification
