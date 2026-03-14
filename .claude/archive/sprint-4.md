# Sprint 4 存档

**Sprint 4 - IpHub 搜索 + 发布**

**目标：** 实现 IpHub CLI 命令（search/info/top）和发布引擎（publish skill/IP 包 → GitHub PR）

**状态：** 已完成

**完成日期：** 2026-03-14

---

## 任务列表

| 优先级 | 任务 | 所属模块 | 状态 |
|-------|------|----------|------|
| P0 | `ipman hub search <query>` 命令 | cli/hub | 已完成 |
| P0 | `ipman hub info <name>` 命令 | cli/hub | 已完成 |
| P1 | `ipman hub top` 命令 | cli/hub | 已完成 |
| P1 | 发布引擎 hub/publisher.py | hub/publisher | 已完成 |
| P1 | `ipman hub publish <name>` Skill 发布 | cli/hub + hub/publisher | 已完成 |
| P1 | `ipman hub publish <file.ip.yaml>` IP 包发布 | cli/hub + hub/publisher | 已完成 |
| P2 | 安装统计上报 | hub/stats | 已完成 |
| P2 | 编写测试 | tests | 已完成 |

---

## 模块状态

| 模块 | 测试数 | 备注 |
|------|--------|------|
| cli/hub (search/info/top) | 8 | IpHub 浏览命令 |
| cli/hub (publish) | 4 | skill + IP 包发布 CLI |
| hub/publisher | 10 | fork → push → PR 引擎 |
| hub/stats | 4 | counter issue 上报 |

**Sprint 4 新增测试总计：26 tests（项目总计 176 tests）**

---

## 关键设计决策

1. **gh CLI 驱动**：所有 GitHub 操作通过 `gh` CLI 执行，复用已有认证，零配置
2. **GitHub API 文件推送**：通过 `gh api PUT contents/` 直接推送文件到 fork 分支，无需 clone
3. **stats 非致命**：安装统计上报失败不影响安装结果
4. **publish 路由**：与 install 一致，通过 `.ip.yaml` 后缀区分 skill 和 IP 包发布
