# 快速上手

## 1. 创建环境

```bash
ipman env create myenv
```

## 2. 激活环境

```bash
ipman env activate myenv
```

Shell 提示符变为 `[ip:myenv]`，表示环境已激活。

## 3. 安装技能

```bash
# 从 IpHub 安装（已经过风险评估）
ipman install web-scraper

# 从本地 IP 包安装（自动触发风险扫描）
ipman install frontend-kit.ip.yaml

# 强制对 IpHub 技能进行本地风险评估
ipman install suspicious-tool --vet

# 以严格安全模式安装
ipman install some-skill --security strict
```

## 4. 查看已安装技能

```bash
ipman skill list
```

## 5. 打包环境

```bash
ipman pack --name my-kit --version 1.0.0
```

生成 `my-kit.ip.yaml` — 可分发的技能包。

## 6. 发布到 IpHub

```bash
ipman hub publish my-kit.ip.yaml
```

## 7. 举报可疑技能

```bash
ipman hub report sketchy-tool --reason "向未知服务器发送数据"
```

## 8. 停用环境

```bash
ipman env deactivate
```
