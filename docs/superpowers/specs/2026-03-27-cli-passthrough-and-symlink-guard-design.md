# CLI Passthrough & Symlink Guard Design

**日期：** 2026-03-27
**状态：** Approved
**涉及模块：** cli/main, cli/skill, core/environment, agents/openclaw, agents/base

---

## 1. 背景与动机

在 Mac Mini 上测试 ipman + OpenClaw 协作时，发现以下问题：

1. **`ipman skill` 只支持 `list` 子命令**：用户无法通过 ipman 执行 agent 的其他 skill 命令（如 `install`、`enable`、`update` 等）
2. **命名不一致**：OpenClaw 用 `skills`（复数），Claude Code 用 `plugin`（单数），ipman 用 `skill`（单数）
3. **`ipman skill list` 遗漏 workspace skills**：通过 `openclaw skills install` 安装的 skill 不出现在列表中
4. **缺少 `plugins` 命令**：ipman 的虚拟环境已纳入 plugins 目录，但无法通过 ipman 管理 plugins
5. **符号链接掉线 bug**：运行 `openclaw plugins install` 后，`.openclaw` 符号链接被破坏，虚拟环境静默退出

---

## 2. 设计概览

采用 **方案 B（Click group + fallback command pattern）** + **增值+保护透传（方案 C）** 的组合。

核心组件：

| 组件 | 职责 |
|------|------|
| `AgentPassthroughGroup` | 自定义 Click Group 子类，未知子命令透传给 agent CLI |
| `symlink_guard` | 上下文管理器，在 agent CLI 调用前后保护符号链接完整性 |
| `_scan_workspace_skills` | OpenClawAdapter 新增 Strategy 4，扫描 workspace skills/ 目录 |

---

## 3. `AgentPassthroughGroup` — 透传 Click Group 基类

### 3.1 类设计

```python
class AgentPassthroughGroup(click.Group):
    """Click group that passes unrecognized subcommands to agent CLI."""

    def __init__(self, *args, agent_cmd_map: dict[str, list[str]], **kwargs):
        super().__init__(*args, **kwargs)
        self.agent_cmd_map = agent_cmd_map

    def resolve_command(self, ctx, args):
        try:
            return super().resolve_command(ctx, args)
        except click.UsageError:
            return "_passthrough", args
```

放在 `src/ipman/cli/passthrough.py` 中。

### 3.2 `_passthrough` handler

```python
@group.command("_passthrough", hidden=True)
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
@click.option("--agent", "agent_name", default=None,
              help="Agent tool to use.")
@click.pass_context
def _passthrough(ctx, args, agent_name):
    # agent_name 来自 --agent 参数或自动探测（复用 cli/_common.py 的 resolve_agent）
    adapter = resolve_agent(agent_name)
    agent_prefix = group.agent_cmd_map[adapter.name]
    full_cmd = agent_prefix + list(args)

    with symlink_guard(project_path):
        result = adapter._run_cli(full_cmd)

    # 输出 agent CLI 的 stdout/stderr
    if result.stdout:
        click.echo(result.stdout, nl=False)
    if result.stderr:
        click.echo(result.stderr, nl=False, err=True)
    ctx.exit(result.returncode)
```

### 3.3 `--help` 处理

- `ipman skills --help`：先输出 ipman 已知子命令的 help，再附加 agent CLI 的 `<prefix> --help` 输出
- `ipman skills <unknown> --help`：走 passthrough，直接透传 `<prefix> <unknown> --help`

### 3.4 命令映射表

```python
# skills group
SKILLS_CMD_MAP = {
    "claude-code": ["claude", "plugin"],
    "openclaw": ["openclaw", "skills"],
}

# plugins group
PLUGINS_CMD_MAP = {
    "claude-code": ["claude", "plugin"],
    "openclaw": ["openclaw", "plugins"],
}
```

---

## 4. 命令注册与别名

### 4.1 注册方式

```python
# cli/main.py
from ipman.cli.passthrough import create_passthrough_group

skills_group = create_passthrough_group(
    name="skills",
    help="Manage skills in the current environment.",
    agent_cmd_map=SKILLS_CMD_MAP,
)

plugins_group = create_passthrough_group(
    name="plugins",
    help="Manage plugins in the current environment.",
    agent_cmd_map=PLUGINS_CMD_MAP,
)

cli.add_command(skills_group, "skills")
cli.add_command(skills_group, "skill")   # alias
cli.add_command(plugins_group, "plugins")
cli.add_command(plugins_group, "plugin")  # alias
```

### 4.2 已知子命令

`skills` group 保留 `list` 子命令（增值逻辑：格式化输出、环境感知）。

### 4.3 与顶层命令的关系

| 命令 | 职责 | 来源 |
|------|------|------|
| `ipman install <source>` | ipman 增值安装（安全扫描、IpHub、IP 文件） | 保留，不动 |
| `ipman uninstall <name>` | ipman 增值卸载 | 保留，不动 |
| `ipman skills install <name>` | 透传给 agent CLI，绕过 ipman 增值逻辑 | 新增（透传） |
| `ipman skills <unknown>` | 透传给 agent CLI | 新增（透传） |
| `ipman plugins <any>` | 纯透传给 agent CLI | 新增（透传） |

用户的选择权：想要安全扫描用 `ipman install`，想要 agent 原生行为用 `ipman skills install`。

---

## 5. `symlink_guard` — 符号链接保护机制

### 5.1 位置

`src/ipman/core/environment.py` 中，作为上下文管理器导出。

### 5.2 逻辑

```python
@contextmanager
def symlink_guard(project_path: Path | None = None):
    project_path = project_path or Path.cwd()

    # 1. 记录当前状态
    config = _read_project_config(project_path)
    if not config or not config.get("active_env"):
        yield
        return

    agent_config_dir = config.get("agent_config_dir", ".claude")
    link_path = project_path / agent_config_dir
    was_symlink = is_symlink(link_path)
    original_target = resolve_symlink(link_path) if was_symlink else None

    yield  # 执行 agent CLI 操作

    # 2. 检查并修复
    if original_target and not is_symlink(link_path):
        if link_path.exists():
            _sync_and_restore_symlink(link_path, original_target, agent_config_dir)
        else:
            create_symlink(target=original_target, link=link_path)
        click.secho(
            "⚠ Environment link was broken by agent CLI operation. Auto-repaired.",
            fg="yellow", err=True,
        )
```

### 5.3 `_sync_and_restore_symlink`

当 agent CLI 将符号链接替换为真实目录时：

1. 将 `link_path`（真实目录）中的新增/修改文件同步到 `original_target`（env 目录）
2. 删除 `link_path`（真实目录）
3. 重建符号链接 `link_path` → `original_target`

同步策略：增量复制（`shutil.copytree(dirs_exist_ok=True)`），不删除 env 中已有的文件。

### 5.4 错误处理

修复失败时（权限等），输出警告但不阻断：

```
⚠ Environment link was broken and auto-repair failed: [Permission denied].
  Run 'ipman env activate <name>' to manually restore.
```

### 5.5 调用点

1. **透传命令**：`_passthrough` handler 中所有 agent CLI 调用
2. **已知命令**：`ipman skills list` 等调用 adapter 的方法时，也包在 `symlink_guard` 内（防御性）

---

## 6. `list_skills` 修复 — workspace skills 扫描

### 6.1 OpenClawAdapter 修改

在现有三步 fallback 之后追加 Strategy 4：

```python
def list_skills(self, workdir: Path | None = None) -> list[SkillInfo]:
    # Strategy 1-3: clawhub list (json / plain / lockfile)
    skills = self._try_clawhub_strategies(workdir)

    # Strategy 4: scan workspace skills/ directory
    workspace_skills = self._scan_workspace_skills(workdir or Path.cwd())
    known_names = {s.name for s in skills}
    for ws in workspace_skills:
        if ws.name not in known_names:
            skills.append(ws)

    return skills
```

### 6.2 `_scan_workspace_skills`

```python
@staticmethod
def _scan_workspace_skills(workdir: Path) -> list[SkillInfo]:
    skills_dir = workdir / "skills"
    if not skills_dir.exists():
        return []
    return [
        SkillInfo(name=entry.name, source="workspace")
        for entry in skills_dir.iterdir()
        if entry.is_dir() and (entry / "SKILL.md").exists()
    ]
```

### 6.3 Claude Code 影响

暂不修改。`claude plugin list --json` 通常是全量的，如后续发现遗漏再补。

---

## 7. 错误处理规范

### 7.1 透传命令失败

```
Error (via OpenClaw): skill 'nonexistent-skill' not found
Exit code: 1
```

- agent CLI 的 stderr 直接输出，前缀 `Error (via <agent_name>):`
- exit code 原样透传

### 7.2 Agent CLI 不存在

```
Error: openclaw command not found. Please install OpenClaw CLI first.
```

复用现有 `_run_cli` 的 `command not found` 逻辑。

---

## 8. 文件变更清单

| 操作 | 文件 | 说明 |
|------|------|------|
| 新建 | `src/ipman/cli/passthrough.py` | AgentPassthroughGroup + 工厂函数 |
| 修改 | `src/ipman/cli/main.py` | 注册 skills/skill/plugins/plugin 命令，移除旧 skill group |
| 修改 | `src/ipman/cli/skill.py` | `list_cmd` 迁移为 skills group 的已知子命令 |
| 修改 | `src/ipman/core/environment.py` | 新增 `symlink_guard` + `_sync_and_restore_symlink` |
| 修改 | `src/ipman/agents/openclaw.py` | 新增 `_scan_workspace_skills`，修改 `list_skills` |
| 新建 | `tests/test_cli/test_passthrough.py` | 透传 group 单元测试 |
| 新建 | `tests/test_core/test_symlink_guard.py` | symlink_guard 单元测试 |
| 修改 | `tests/test_agents/test_openclaw.py` 或同目录 | workspace skills 扫描测试 |
| 修改 | `tests/e2e/test_openclaw_compat.py` | 新增 passthrough / plugins / alias e2e 测试，xfail → pass |

---

## 9. 测试计划

### 9.1 单元测试

| 测试文件 | 场景 |
|---|---|
| `test_passthrough.py` | 已知命令正常分发；未知命令走 passthrough；`--help` 转发；别名 skill=skills |
| `test_symlink_guard.py` | 无活跃环境 → no-op；链接完好 → no-op；链接被破坏 → 自动修复；链接和目录都消失 → 重建；修复失败 → 警告不阻断 |
| `test_openclaw.py` | workspace skills/ 扫描；与 clawhub 结果去重；空目录 → 空列表；无 SKILL.md 的目录 → 跳过 |

### 9.2 E2E 测试

| 测试 | 场景 |
|---|---|
| `test_skills_passthrough_unknown_cmd` | `ipman skills <unknown>` 透传到 mock agent CLI |
| `test_skills_list_includes_workspace` | `ipman skills list` 包含 workspace skills/ 中的 skill |
| `test_plugins_passthrough` | `ipman plugins install` 透传到 mock agent CLI |
| `test_skill_alias` | `ipman skill list` 等价于 `ipman skills list` |
| `test_env_survives_symlink_replacement` | 从 xfail 改为 pass（symlink_guard 修复后） |

---

## 10. 向后兼容

| 变更 | 兼容性 |
|------|--------|
| `ipman skill list` | 保持工作（`skill` 是 `skills` 的别名） |
| `ipman install` / `ipman uninstall` | 不受影响，保持原有增值逻辑 |
| `ipman skill list` 输出格式 | 不变 |
| 新增 `ipman skills` / `ipman plugins` | 纯新增，无破坏 |
