# Sprint 3 存档

**Sprint 3 - IP 包格式 + 打包/安装**

**目标：** 定义 IP 包 YAML schema，实现打包（pack）、安装（install from file）、IpHub 安装、依赖解析

**状态：** 已完成

**完成日期：** 2026-03-14

---

## 任务列表

| 优先级 | 任务 | 所属模块 | 状态 |
|-------|------|----------|------|
| P0 | 定义 IP 包 YAML schema（本地 .ip.yaml 文件格式） | core/package | 已完成 |
| P0 | 实现 IP 包解析器（加载 + 校验） | core/package | 已完成 |
| P0 | 实现 `ipman pack` 命令（从环境生成 .ip.yaml，合并原 export） | CLI + core | 已完成 |
| P1 | 实现 `ipman install <file.ip.yaml>` 本地 IP 文件安装 | CLI + core | 已完成 |
| P1 | 实现 `ipman install <short-name>` 基于 IpHub 的在线安装 | CLI + hub + core | 已完成 |
| P1 | 实现依赖解析引擎（版本匹配 + 递归依赖 + 循环检测） | core/resolver | 已完成 |
| P2 | IP 文件头部自动注入 IpMan 引用和安装说明 | core/package | 已完成 |
| P2 | 编写 IP 包解析/打包/安装/依赖解析测试 | tests | 已完成 |

---

## 模块状态

| 模块 | 测试数 | 备注 |
|------|--------|------|
| core/package | 16 | IP schema + 解析 + 序列化 |
| core/resolver | 19 | 版本匹配 + 递归解析 + 循环检测 |
| cli/pack | 10 | pack 命令（合并原 export） |
| cli/install (IP file) | 8 | .ip.yaml 本地安装 |
| cli/install (IpHub) | 7 | 短名称 IpHub 安装 + fetch_registry |
| hub/client (fetch_registry) | 3 | 注册文件获取 |

**Sprint 3 新增测试总计：63 tests（项目总计 150 tests）**

---

## 关键设计决策

1. **合并 pack 和 export**：两者语义重叠，合并为单一 `ipman pack` 命令
2. **install 三路由**：`.ip.yaml` 文件 → 本地安装；短名称 → IpHub 查询安装；自动判断
3. **Resolver 函数式设计**：使用 `fetcher` 回调解耦 I/O，纯逻辑可测
4. **版本约束四种语法**：`==`（精确）、`>=`、`^`（兼容）、`~`（补丁）
