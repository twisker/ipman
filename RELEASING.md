# Release Guide

IpMan 发布流程，基于 Git Flow + GitHub Actions 自动化。

## Prerequisites

```bash
# Git Flow 初始化（如未初始化）
git flow init -d

# 配置 tag 自动加 v 前缀（一次性）
git config --global gitflow.prefix.versiontag v
```

## Release Steps

### 1. Create Release Branch

```bash
git flow release start 0.2.0
```

从 `dev` 分支创建 `release/0.2.0`。

### 2. Finalize Version

```bash
# Minor 版本升级（自动 commit）
bash scripts/bump-minor.sh

# 或 Major 版本升级
# bash scripts/bump-major.sh
```

此时可做最后调整：更新文档、修复 last-minute 问题等。

### 3. Finish Release

```bash
git flow release finish 0.2.0
```

会弹出编辑器填写 tag message，保存即可。此命令自动完成：

- 合并 `release/0.2.0` → `main`
- 合并 `release/0.2.0` → `dev`
- 创建 tag `v0.2.0`（因为配置了 versiontag 前缀）
- 删除 `release/0.2.0` 分支

### 4. Push

```bash
git push origin main dev --tags
```

### 5. Automated (GitHub Actions)

推送 `v*` tag 后，自动触发 `.github/workflows/publish.yml`：

| Job | 动作 |
|-----|------|
| **release** | git-cliff 生成变更日志 → 创建 GitHub Release |
| **publish** | 构建 wheel → 发布到 PyPI (`ipman-cli`) |
| **binaries** | PyInstaller 打包 Linux/macOS/Windows → 上传到 Release |

## Hotfix

```bash
git flow hotfix start 0.2.1
# 修复 bug
echo "0.2.1" > VERSION
git add VERSION && git commit -m "fix: description of fix"
git flow hotfix finish 0.2.1
git push origin main dev --tags
```

## Version Numbering

- `VERSION` 文件为唯一版本源
- 开发期间 patch 由 pre-commit hook 自动递增（`.githooks/pre-commit` → `scripts/bump-patch.sh`）
- 发布时使用脚本设置正式版本号：
- `pyproject.toml` 通过 hatchling 动态读取 `VERSION`
- `__init__.py` 通过 `importlib.metadata` 读取安装元数据

### 版本号脚本

```bash
# Minor 版本升级（如 0.1.x → 0.2.0），重置 patch 为 0
bash scripts/bump-minor.sh

# Major 版本升级（如 0.x.x → 1.0.0），重置 minor 和 patch 为 0
bash scripts/bump-major.sh

# Patch 自动递增（每次 commit 由 pre-commit hook 自动调用，无需手动执行）
# bash scripts/bump-patch.sh
```

发布时推荐流程：在 release 分支上调用 `bump-minor.sh` 或 `bump-major.sh`，而非手动编辑 `VERSION` 文件。

## Checklist

发布前确认：

- [ ] 所有测试通过：`uv run pytest`
- [ ] 代码质量通过：`uv run ruff check src/ tests/`
- [ ] 类型检查通过：`uv run mypy src/ipman/`
- [ ] VERSION 文件已更新
- [ ] PyPI Trusted Publisher 已配置（首次发布需要）
