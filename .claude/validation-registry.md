# 验收标准登记表

此文件记载各模块的交付标准或验收标准。包括通用交付标准，以及各模块的专项验收标准。

---

## 通用交付标准

所有交付物必须满足以下标准：

### 代码质量

| 标准 | 要求 |
|------|------|
| ruff 检查 | 无 error，无 warning |
| mypy 类型检查 | strict 模式通过 |
| 测试通过 | 所有测试用例 100% 通过 |
| 测试覆盖率 | 核心逻辑 >= 80% |

### 功能完整性

| 标准 | 要求 |
|------|------|
| 需求覆盖 | PRD 中标注的功能均已实现 |
| 边界处理 | 异常路径和空状态有合理处理 |
| 跨平台 | Linux、macOS、Windows 三平台行为一致 |

### 性能

| 标准 | 要求 |
|------|------|
| CLI 冷启动 | < 500ms |
| 单技能安装（本地） | < 5s |
| 单技能安装（网络） | < 15s |
| 依赖解析 | 50 个依赖 < 3s |

### 基础设施与部署

| 标准 | 要求 |
|------|------|
| CI 通过 | 三平台 CI 矩阵全部绿色 |
| PyPI 发布 | `pip install ipman` 可正常安装并运行 |

---

## 模块专项验收标准

### 虚拟环境管理（core/environment）

- `ipman create` 在 project/user/machine 三个 scope 下均能正确创建环境
- 环境目录结构正确，元数据文件完整
- `ipman activate` 后命令行提示符有醒目变化
- `ipman deactivate` 恢复原始提示符
- `ipman delete` 正确清理所有软链接和环境文件
- 多环境并存互不干扰

### Agent 适配（agents/）

- 能自动探测本机已安装的 Agent 工具及版本
- 能根据项目目录结构猜测所用 Agent
- `--agent` 参数能正确覆盖自动探测
- 适配器操作不侵入 Agent 内部目录

### 技能管理（通过 Agent CLI）

- `ipman install` 正确调用当前 agent 的原生 CLI 命令完成安装
- `ipman uninstall` 正确调用当前 agent 的原生 CLI 命令完成卸载
- `ipman skill list` 正确调用当前 agent 的原生 CLI 命令列出已安装技能
- 不直接操作 agent 内部目录结构，所有 CRUD 通过 agent CLI 执行
- 支持通过 `--agent` 参数手动指定 agent，覆盖自动探测

### IP 包管理（core/package）

- IP 文件符合 YAML schema 定义
- 自动生成的 IP 文件头部包含 IpMan 引用和安装说明
- 依赖递归解析正确
- 循环依赖能检测并报错

### IpHub（hub/）

- 能正确拉取并缓存 index.yaml
- 搜索基于本地 index.yaml 过滤，返回结果准确
- 安装流程：解析引用 → 调用 agent CLI 原生命令 → 计数
- 发布流程：读取 gh 身份 → fork iphub → 创建注册文件 → 提 PR
- 身份认证基于 GitHub PR author（gh CLI token）
- 安装计数通过 GitHub Issue comment + reaction 实现

### 国际化（utils/i18n）

- 检测到 `LANG=zh*` 时自动切换中文
- 所有用户可见文本均有中英双语
- 帮助文档中英双语完整
