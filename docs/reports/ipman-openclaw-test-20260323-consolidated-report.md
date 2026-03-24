# `ipman` × `OpenClaw` 综合测试报告（非 Claude 功能）

日期：2026-03-22 ~ 2026-03-23  
执行人：subagent `ipman-test` + 没事嗯嗯  
关联原始报告：
- `reports/ipman-openclaw-test-20260322/report.md`
- `reports/ipman-openclaw-test-20260323-followup-report.md`

## 1. 结论先行

结论一句话：

> **除 Claude 功能本身外，`ipman 0.1.88` 面向 `OpenClaw` 的核心命令面已经基本测全；当前主要问题不是“还有哪块没测”，而是“已经测到的关键链路存在多处系统性不对齐”。**

综合评级：

- `OpenClaw` 适配：**不合格 / 仅部分可用**
- 本地环境适应性：**中等偏弱**
- 环境管理：**create / activate / deactivate / inherit / restore / delete 可用，但 layering / machine scope / 隔离边界有明显问题**
- skill 安装：**可部分安装，但安装落点与 env / OpenClaw 发现模型脱节**
- skill 列表与打包：**当前实装链路基本失效**
- 卸载：**非交互场景不可用**
- hub 读链路：**search / info / top / report 均受 `index_url` 覆盖缺陷影响**
- hub 写链路：**`publish` 真实外写已成功；`report` 的真实外写在当前 upstream 配置下失败（缺少 `report` label）**

## 2. 测试环境

- 主机：`dayu的Mac mini`
- OS：`Darwin 25.3.0 (arm64)`
- Shell：`zsh`
- `ipman`：`0.1.88`
- `openclaw`：`2026.3.13 (61d171a)`
- `clawhub`：`0.8.0`
- `python3`：`3.14.3`
- 工作区：`/Users/xkool/.openclaw/workspace`

关键环境现象：

- `ipman` 安装在 Python user-site：`~/Library/Python/3.14/lib/python/site-packages`
- 启动脚本：`~/.local/bin/ipman`
- 切换 `HOME` 后若不补 `PYTHONPATH`，`ipman` 无法启动
- 当前机器对 `raw.githubusercontent.com` 的 Python `urllib` 证书校验失败

## 3. 测试范围与边界

本轮覆盖：

- `OpenClaw` 适配
- 本地环境适应性
- 环境创建 / 激活 / 继承 / 删除 / 状态 / layering
- OpenClaw skill 安装 / 卸载 / 列举 / 打包
- package 安装
- 本地 `.ip.yaml` 安装与风控
- `hub search / info / top / publish / report`
- `clawhub` 与 `openclaw` 的关键联动探针

明确不测的部分：

- **不测试 Claude 功能本身**

真实外写补充说明（2026-03-23）：

- `ipman hub publish`：已做真实外写验证，成功创建公开 PR：`https://github.com/twisker/iphub/pull/8`
- `ipman hub report`：已做真实外写验证，但真实执行失败，错误为：`could not add label: 'report' not found`
- 因当前机器上 Python `urllib` 对 GitHub Raw 有 SSL 问题，`report` 真实测试前用 live `index.yaml` 预热了本地 cache，只为走到真正的 `gh issue create` 步骤

## 4. 覆盖情况总览

除 Claude 功能外，当前已覆盖的核心命令面如下：

- `ipman info`
- `ipman env create`
- `ipman env activate`
- `ipman env deactivate`
- `ipman env delete`
- `ipman env list`
- `ipman env status`
- `ipman install`（skill / package / local file / dry-run / security 分支）
- `ipman uninstall`
- `ipman skill list`
- `ipman pack`
- `ipman hub search`
- `ipman hub info`
- `ipman hub top`
- `ipman hub publish`
- `ipman hub report`

结论：**没有再发现“核心功能完全没测到”的空白项。**

真实外写结论补充：

- `publish`：真实成功
- `report`：真实失败，失败点不是命令找不到或鉴权缺失，而是 upstream `twisker/iphub` 仓库当前不存在 `report` label

## 5. 主要测试结论

### 5.1 可用部分

这些链路在当前环境下基本成立：

- `ipman` / `openclaw` / `clawhub` 基线命令可执行
- `ipman env create --agent openclaw` 可创建环境
- `ipman env activate` / `deactivate` 可完成 `.openclaw` 的备份与恢复
- `ipman env create --inherit` 的目录复制逻辑成立
- `ipman env delete --yes` 可删除 project scope 环境
- 本地 `.ip.yaml` 的风险扫描与默认阻断逻辑基本有效
- `ipman hub publish` 的 package PR workflow 已做真实外写验证，并成功创建 PR：`https://github.com/twisker/iphub/pull/8`
- `ipman hub report` 的 issue 创建命令组装在本地假 `gh` 下成立；真实外写时则被 upstream repo 配置阻断：`could not add label: 'report' not found`

### 5.2 明显失效或不对齐部分

这些链路要么失败，要么逻辑与 OpenClaw / ClawHub 当前行为不一致：

- `HOME` 隔离下 `ipman` 无法自举
- OpenClaw 新项目默认 agent 会回退到 `claude-code`
- machine scope 默认落到 `/opt/ipman/envs`，普通 macOS 用户不可用
- `IPMAN_HUB_URL` 不能完整覆盖 index 来源
- OpenClaw adapter 的安装落点在项目根 `skills/`，不在 `.openclaw/skills/`
- `ipman skill list` 依赖 `clawhub list --json`，但 `clawhub 0.8.0` 不支持该参数
- `ipman pack` 因依赖空的 skill list 导致打出空包
- `ipman uninstall` 不透传 `--yes`，非交互场景失败
- risk install 不透传 `--force`
- repo 子目录安装不透传 `--workdir`
- multi-scope layering 的文案与实现不一致
- 临时项目根 `skills/` 中的 skill 未被 `openclaw skills info` 识别

## 6. 关键根因归纳

### 根因 A：OpenClaw adapter 与 `clawhub 0.8.0` CLI 未对齐

表现：

- 调 `clawhub list --json` 失败
- `uninstall` 缺 `--yes`
- risk install 缺 `--force`
- repo 内安装缺 `--workdir`

影响：

- `skill list` 失效
- `pack` 失效
- `uninstall` 失效
- 安装可能误写到错误目录

### 根因 B：环境隔离模型与 skill 实际落点脱节

表现：

- env 激活切换的是 `.openclaw`
- 实际 skill 却被 `clawhub install` 装到项目根 `skills/`

影响：

- activation / deactivation 对 skill 隔离几乎无意义
- `.openclaw` env 和项目根 `skills/` 形成两套彼此脱节的系统
- 当前 OpenClaw 也未可靠识别这套落点

### 根因 C：`IpHubClient` 只覆盖 `base_url`，不覆盖 `index_url`

表现：

- `IPMAN_HUB_URL` 无法完整替代默认 GitHub Raw 索引
- 缓存一旦过期，`search / info / top / report` 都会回退到 `raw.githubusercontent.com`

影响：

- 当前机器上会再次触发 SSL 证书失败
- `hub` 读链路并不稳定，且依赖缓存状态

### 根因 D：安装形态过度依赖 user-site + 当前 `HOME`

表现：

- 切换 `HOME` 后需要额外补 `PYTHONPATH`

影响：

- 隔离测试脆弱
- 容器 / sandbox / 多 home 环境下可移植性差

## 7. 精简缺陷清单

下面这份清单按“适合提 issue / 排优先级”的方式压缩整理。

### P0：必须先修

1. **OpenClaw adapter 调用了不兼容的 `clawhub` CLI 参数**
   - 现象：`ipman skill list` 依赖 `clawhub list --json`，而 `clawhub 0.8.0` 不支持 `--json`
   - 影响：`skill list` 直接失效，`pack` 连带打空包
   - 建议：改为解析 `clawhub list` 输出，或直接读取 `.clawhub/lock.json`

2. **OpenClaw adapter 未透传 `--yes`，导致 `uninstall` 非交互失败**
   - 现象：`ipman uninstall find --agent openclaw` 报 `Pass --yes (no input)`
   - 影响：CI / agent / subagent 场景不可用，且容易留下残留 skill
   - 建议：在 adapter 的卸载路径强制透传 `--yes`

3. **OpenClaw adapter 未透传 `--force`，导致 risk install 逻辑断链**
   - 现象：上层 permissive 或包内风险允许后，底层 `clawhub` 仍因缺 `--force` 拒绝安装
   - 影响：策略上允许、执行上失败，行为不一致
   - 建议：为 OpenClaw adapter 增加 `--force` 透传能力

4. **OpenClaw adapter 未透传 `--workdir`，repo 内安装目标可能落到仓库根**
   - 现象：在 git repo 子目录中执行时，`clawhub` 默认 workdir 被 repo 根影响
   - 影响：可能误写主仓库根目录 `skills/`
   - 建议：显式传 `--workdir $(pwd)` 或等价当前测试目录

5. **skill 实际安装落点与 `.openclaw` env 模型脱节**
   - 现象：env 管的是 `.openclaw`，安装却落在项目根 `skills/`
   - 影响：环境隔离失效，OpenClaw 发现模型也未可靠对齐
   - 建议：统一 OpenClaw skill 的真实落点与 env 边界

6. **`IPMAN_HUB_URL` 不能覆盖 `index_url`，导致整个 `hub` 读链路不稳定**
   - 现象：`search / info / top / report` 在缓存过期后回落到默认 GitHub Raw 索引
   - 影响：当前机器上会重复触发 SSL 失败；Hub 覆盖方案不完整
   - 建议：让 `IPMAN_HUB_URL` 同时覆盖 `base_url` 与 `index_url`

7. **`ipman hub report` 在当前 upstream 上真实不可用：硬编码的 `report` label 不存在**
   - 现象：真实执行 `ipman hub report twisker-test --reason ...` 返回 `could not add label: 'report' not found`
   - 影响：真实 issue 创建路径被直接阻断，功能在当前官方仓库配置下不可用
   - 建议：要么在 `twisker/iphub` 预置 `report` label，要么让 `ipman hub report` 在 label 不存在时降级为无 label 创建

### P1：高优先修

8. **OpenClaw 新项目默认 agent 自动检测会回退到 `claude-code`**
   - 现象：无 `.openclaw` / `.claude` 的新目录里，`ipman env create` 默认写出 `claude-code`
   - 影响：OpenClaw 用户首次体验错误，容易误配
   - 建议：在 OpenClaw 场景明确优先级，或要求显式 agent 并给出提示

9. **machine scope 在 macOS 上默认不可用**
   - 现象：硬编码 `/opt/ipman/envs`，普通用户权限不足
   - 影响：machine scope 实际不可落地
   - 建议：支持可配置 machine env 根路径，或提供更友好的回退与报错

10. **multi-scope layering 的实现与文案不一致**
   - 现象：文案像是支持 machine/user/project 叠加，实际只有单 `active_env` 覆盖
   - 影响：用户心智模型和真实行为不一致
   - 建议：要么实现真正 layering，要么把文档和状态输出改成单 active env 语义

11. **`ipman` 安装形态依赖 user-site + `HOME`，隔离能力弱**
    - 现象：切换 `HOME` 后直接 `ModuleNotFoundError`
    - 影响：隔离测试、容器测试、临时 HOME 场景脆弱
    - 建议：改善安装分发方式，或让运行时更稳定定位自身依赖

### P2：建议优化

12. **缺少 OpenClaw 端到端自检能力**
    - 建议：增加检查当前 workspace、skills 发现路径、ClawHub lockfile、adapter CLI 兼容性的自检命令

13. **`pack` 缺少绕过 `skill list` 的兜底模式**
    - 建议：增加“从 `.clawhub/lock.json` 打包”的显式模式

## 8. 风险评估

### 已控制的风险

- 安装 / 环境测试尽量都在 `/tmp` 下完成，避免污染当前主工作区
- `ipman hub publish` 已完成真实外写验证，并成功创建 PR
- `ipman hub report` 已完成真实外写验证，但在当前 upstream 配置下因缺少 `report` label 而失败
- 风险 skill 在独立临时目录中验证

### 仍需注意的风险

- 在真实 repo 中直接跑安装，仍可能误写仓库根 `skills/`
- `ipman uninstall` 当前失败会让自动化残留 skill
- permissive 风控与底层强制参数不一致，容易制造“允许但没装上”的假象
- `hub` 读命令目前受缓存状态影响，稳定性不足

## 9. 建议修复顺序

建议按下面顺序推进：

1. 先修 OpenClaw adapter：`list` / `install` / `uninstall` / `pack` 的 `clawhub` 对接
2. 补齐 `--yes` / `--force` / `--workdir` 透传
3. 修 `IpHubClient`，让 `IPMAN_HUB_URL` 同时覆盖 `index_url` 与 `base_url`
4. 明确 OpenClaw skill 的真实落点：项目根 `skills/`、`.openclaw/skills/`，还是别的 workspace 模型
5. 再回头处理 machine scope、layering、安装形态等结构性问题

## 10. 复现与证据入口

- 主脚本：`reports/ipman-openclaw-test-20260322/run_tests.sh`
- 原始主报告：`reports/ipman-openclaw-test-20260322/report.md`
- 原始补测报告：`reports/ipman-openclaw-test-20260323-followup-report.md`
- 整合报告：`reports/ipman-openclaw-test-20260323-consolidated-report.md`
- 日志目录：`reports/ipman-openclaw-test-20260322/logs/`
- 假 GH 记录：`reports/ipman-openclaw-test-20260322/artifacts/fake-gh.log`

## 11. 最终判断

如果目标是把 `ipman` 当作 `OpenClaw` skill 的隔离环境管理器来用，那么当前版本还不够稳。

更准确地说：

> **`ipman 0.1.88` 现在更像“对 ClawHub 做了一个未完全对齐的壳”，而不是一个已经与 OpenClaw skill 发现、安装、卸载、打包、Hub 读写路径稳定对齐的环境管理器。**

它不是完全不能用，但在自动化、隔离测试、风险 skill、repo 内安装、Hub 覆盖这些关键场景里，都还有明显的产品级断点。