# 安全指南

IpMan 内置针对恶意 AI Agent 技能的防御能力。

## 为什么重要？

- ClawHub 上 36% 的技能包含 prompt 注入（[Snyk ToxicSkills](https://snyk.io/blog/toxicskills-malicious-ai-agent-skills-clawhub/)）
- 技能以 Agent 完整权限运行，默认无沙箱
- 攻击手法：凭证窃取、数据外泄、混淆代码执行

## 风险级别

| 级别 | 含义 | 示例 |
|------|------|------|
| LOW | 未检测到问题 | 笔记、格式化、天气 |
| MEDIUM | 存在关注点 | 文件操作、API 调用 |
| HIGH | 检测到红旗 | 凭证访问、系统修改 |
| EXTREME | 可能恶意 | Root 访问、数据外泄 |

## 安全模式

```bash
ipman install web-scraper --security strict
```

| 模式 | LOW | MEDIUM | HIGH | EXTREME |
|------|-----|--------|------|---------|
| `permissive` | 安装 | 安装 | 安装 | 告警 |
| `default` | 安装 | 安装 | 告警 | 阻止 |
| `cautious` | 安装 | 告警 | 阻止 | 阻止 |
| `strict` | 安装 | 确认 | 阻止 | 阻止 |

在 `~/.ipman/config.yaml` 中设置默认模式：

```yaml
security:
  mode: cautious
```

## 信任模型

| 来源 | 默认行为 |
|------|---------|
| IpHub | 信任已有风险标注 |
| 本地 `.ip.yaml` 文件 | 强制本地扫描 |
| URL / 自定义 hub | 强制本地扫描 |

覆盖参数：

```bash
ipman install hub-skill --vet        # 强制本地扫描
ipman install local.ip.yaml --no-vet # 跳过本地扫描
```

## 安全日志

被阻止和告警的安装记录在 `~/.ipman/security.log`：

```
2026-03-14T10:30:00Z BLOCK sketchy-tool source=local risk=EXTREME
```

通过配置禁用：

```yaml
security:
  log_enabled: false
```

## 举报可疑技能

```bash
ipman hub report sketchy-tool --reason "无故访问 ~/.ssh"
```

举报次数纳入风险评分参考，并在 `ipman hub info` 中公开展示。
