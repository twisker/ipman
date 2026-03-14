# 当前 Sprint

**Sprint 4 - IpHub 搜索 + 发布**

**目标：** 实现 IpHub CLI 命令（search/info/top）和发布引擎（publish skill/IP 包 → GitHub PR）

**状态：** 进行中

---

## 前置条件

- [x] Sprint 3 已完成并存档
- [x] IpHub 设计方案已确认（`.claude/research/iphub-design.md`）
- [x] IpHubClient 基础已实现（fetch_index/search/lookup/fetch_registry）
- [x] `twisker/iphub` GitHub 仓库已创建（H02）
- [x] `gh` CLI 已安装认证（H03）

---

## 任务列表

| 优先级 | 任务 | 所属模块 | 责任人 | 状态 |
|-------|------|----------|--------|------|
| P0 | 实现 `ipman hub search <query>` 命令 | cli/hub | AI | 待开始 |
| P0 | 实现 `ipman hub info <name>` 命令 | cli/hub | AI | 待开始 |
| P1 | 实现 `ipman hub top` 命令 | cli/hub | AI | 待开始 |
| P1 | 实现发布引擎 hub/publisher.py | hub/publisher | AI | 待开始 |
| P1 | 实现 `ipman hub publish <name>` Skill 发布 | cli/hub + hub/publisher | AI | 待开始 |
| P1 | 实现 `ipman hub publish <file.ip.yaml>` IP 包发布 | cli/hub + hub/publisher | AI | 待开始 |
| P2 | 安装统计上报（counter issue comment + reaction） | hub/stats | AI | 待开始 |
| P2 | 编写 IpHub CLI + publisher 测试 | tests | AI | 进行中 |

---

## 模块状态

| 模块 | 状态 | 最后更新 | 当前目标 | 备注 |
|------|------|---------|---------|------|
| cli/hub | 待开始 | -- | search/info/top/publish 命令 | 新模块 |
| hub/publisher | 待开始 | -- | fork → 注册文件 → PR | 新模块 |
| hub/stats | 待开始 | -- | counter issue 上报 | 新模块 |

---

## 活跃文件清单

- `src/ipman/hub/client.py` — IpHub 客户端（已有，待扩展）
- `src/ipman/cli/hub.py` — IpHub CLI 命令（新建）
- `src/ipman/hub/publisher.py` — 发布引擎（新建）

---

## 近期改动记录

| 时间 | 改动目的 | 涉及模块/文件 |
|------|---------|-------------|
| 2026-03-14 | Sprint 4 初始化 | .claude/current-sprint.md |
