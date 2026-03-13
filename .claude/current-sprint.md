# 当前 Sprint

**Sprint 3 - IP 包格式 + 打包/安装**

**目标：** 定义 IP 包 YAML schema，实现打包（pack）、安装（install from file）、导出（export）、依赖解析

**状态：** 进行中

---

## 前置条件

- [x] Sprint 2 已完成并存档
- [x] IpHub 注册文件格式已设计（`.claude/research/iphub-design.md` 第三节）
- [x] PRD FR11-FR15 需求明确
- [ ] 设计方案经人工确认

---

## 任务列表

| 优先级 | 任务 | 所属模块 | 责任人 | 状态 |
|-------|------|----------|--------|------|
| P0 | 定义 IP 包 YAML schema（本地 .ip.yaml 文件格式） | core/package | AI | 待开始 |
| P0 | 实现 IP 包解析器（加载 + 校验） | core/package | AI | 待开始 |
| P0 | 实现 `ipman pack` 命令（从环境生成 .ip.yaml） | CLI + core | AI | 待开始 |
| P1 | 实现 `ipman install <file.ip.yaml>` 本地 IP 文件安装 | CLI + core | AI | 待开始 |
| P1 | 实现 `ipman install <short-name.ip>` 基于 IpHub 的在线 IP 包安装 | CLI + hub + core | AI | 待开始 |
| P1 | 实现依赖解析引擎（版本匹配 + 递归依赖 + 循环检测） | core/resolver | AI | 待开始 |
| P1 | 实现 `ipman export` 命令（导出当前环境为 IP 文件） | CLI + core | AI | 待开始 |
| P2 | IP 文件头部自动注入 IpMan 引用和安装说明 | core/package | AI | 待开始 |
| P2 | 编写 IP 包解析/打包/安装/依赖解析测试 | tests | AI | 待开始 |

---

## 模块状态

| 模块 | 状态 | 最后更新 | 当前目标 | 备注 |
|------|------|---------|---------|------|
| core/package | 待开始 | -- | IP schema + 解析 + 打包 | 新模块 |
| core/resolver | 待开始 | -- | 版本匹配 + 依赖解析 | 新模块 |
| cli/pack | 待开始 | -- | pack/export 命令 | 新模块 |

---

## 活跃文件清单

（待开发启动后填充）

---

## 近期改动记录

| 时间 | 改动目的 | 涉及模块/文件 |
|------|---------|-------------|
| 2026-03-14 | Sprint 2 存档，Sprint 3 初始化 | .claude/archive/sprint-2.md |
