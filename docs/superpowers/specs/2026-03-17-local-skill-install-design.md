# Local Skill Install Support — Design Spec

> IpMan - Intelligence Package Manager
> Date: 2026-03-17
> Status: Approved
> Sprint: 7 B-group (Phase 4 — User Experience Improvement)

## 1. Background & Motivation

`ipman install` currently accepts only two source types: `.ip.yaml` file paths and IpHub names. Users cannot install a local skill directory (e.g. `ipman install ./my-skill/`), forcing them to use agent-native CLIs directly. This breaks the ipman abstraction and leaves 3 E2E tests permanently skipped.

## 2. SOURCE Type Detection

Extend `ipman install <SOURCE>` to auto-detect three types:

```python
def _classify_source(source: str) -> str:
    """Classify install source type."""
    if source.endswith(".ip.yaml"):
        return "ip_file"
    path = Path(source)
    if path.exists() and (path.is_dir() or path.is_file()):
        return "local_skill"
    return "hub_name"
```

Priority: `.ip.yaml` suffix check first (explicit), then filesystem existence, then fallback to hub name.

## 3. Agent Adapter Changes

### 3.1 ClaudeCodeAdapter.install_skill()

Current: always runs `claude plugin install <name>`.

New: detect local path vs remote name.

```python
def install_skill(self, name: str, **kwargs):
    path = Path(name)
    if path.exists():
        # Local path — use claude mcp add or plugin add
        args = ["claude", "mcp", "add", str(path.resolve())]
    else:
        # IpHub name — use plugin install
        args = ["claude", "plugin", "install", name]
    scope = kwargs.get("scope")
    if scope:
        args.extend(["-s", scope])
    return self._run_cli(args)
```

Note: `claude mcp add` is the current recommended way to add local skills/plugins. If this fails on CI, the E2E tests will skip gracefully (existing FileNotFoundError handling in AgentManager).

### 3.2 OpenClawAdapter.install_skill()

Current: always runs `clawhub install <name>`.

New: detect local path and copy to skills directory.

```python
def install_skill(self, name: str, **kwargs):
    path = Path(name)
    if path.exists():
        # Local path — copy to skills/ directory
        dest = Path.cwd() / "skills" / path.name
        if path.is_dir():
            shutil.copytree(path, dest, dirs_exist_ok=True)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)
        return subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    else:
        # IpHub name — use clawhub install
        return self._run_cli(["clawhub", "install", name])
```

### 3.3 Uninstall — no changes needed

`uninstall_skill(name)` takes a skill name, not a path. No changes required.

## 4. CLI Install Command Changes

In `src/ipman/cli/skill.py`, the `install()` function:

```python
source_type = _classify_source(source)

if source_type == "local_skill":
    if not dry_run:
        result = adapter.install_skill(source)
        if result.returncode == 0:
            click.secho(f"Installed local skill from '{source}'.", fg="green")
        else:
            msg = result.stderr.strip() or result.stdout.strip() or "Unknown error"
            click.secho(f"Install failed: {msg}", fg="red", err=True)
            raise SystemExit(1)
    else:
        click.echo(f"Would install local skill: {source}")
elif source_type == "ip_file":
    _install_from_ip_file(Path(source), adapter, dry_run=dry_run)
else:
    _install_from_hub(source, adapter, dry_run=dry_run)
```

Security vetting for local skills: the existing vet logic already handles local files. For directories, vet the contents of key files (SKILL.md, etc.) if `should_vet` is True.

## 5. E2E Test Updates

### 5.1 Unlock skipped tests

The 3 tests in `tests/e2e/test_skill_install.py` currently call `pytest.skip("Local skill directory install not yet supported")`. After this change:

- `test_install_skill_from_local`: call `run_ipman("install", str(fixture_path), "--agent", agent)` or use `agent_manager.install_skill()`
- `test_uninstall_skill`: install first, then `run_ipman("uninstall", "e2e-hello-world", "--agent", agent)`
- `test_skill_persists_across_deactivate_reactivate`: install, deactivate, reactivate, verify

### 5.2 Fixture structure

Current fixtures at `tests/e2e/fixtures/skills/<agent>/hello-world/SKILL.md` are simple markdown files. This structure is sufficient:
- Claude Code adapter will pass the directory path to `claude mcp add`
- OpenClaw adapter will copy the directory to `skills/`

No structural changes needed to fixtures.

## 6. Backward Compatibility

- Existing `ipman install skill-name` (hub) — unchanged
- Existing `ipman install file.ip.yaml` (IP file) — unchanged
- New `ipman install ./my-skill/` (local dir) — new behavior
- Agent adapters: remote install path unchanged, local path is additive

## 7. Production Code Changes

| File | Action | Description |
|------|--------|-------------|
| `src/ipman/cli/skill.py` | Modify | Add `_classify_source()`, add `local_skill` branch in `install()` |
| `src/ipman/agents/claude_code.py` | Modify | `install_skill()` detect local path vs remote name |
| `src/ipman/agents/openclaw.py` | Modify | `install_skill()` local path → file copy |
| `tests/test_agents/test_adapters_cli.py` | Modify | Add tests for local path install |
| `tests/test_cli/test_skill.py` | Modify | Add test for `_classify_source()` and local_skill CLI branch |
| `tests/e2e/test_skill_install.py` | Modify | Unlock 3 skipped tests |

## 8. Test Scenarios

### Unit tests (test_adapters_cli.py)

| Test | Description |
|------|-------------|
| `test_claude_install_local_path` | Local dir → `claude mcp add` called |
| `test_claude_install_remote_name` | Hub name → `claude plugin install` called |
| `test_openclaw_install_local_dir` | Local dir → copied to skills/ |
| `test_openclaw_install_local_file` | Local file → copied to skills/ |
| `test_openclaw_install_remote_name` | Hub name → `clawhub install` called |

### Unit tests (test_skill.py)

| Test | Description |
|------|-------------|
| `test_classify_source_ip_file` | `.ip.yaml` → "ip_file" |
| `test_classify_source_local_dir` | Existing dir → "local_skill" |
| `test_classify_source_local_file` | Existing file → "local_skill" |
| `test_classify_source_hub_name` | Non-existent path → "hub_name" |

### E2E tests (test_skill_install.py) — unlocked

| Test | Description |
|------|-------------|
| `test_install_skill_from_local` | Install fixture dir via `ipman install` or adapter |
| `test_uninstall_skill` | Install then uninstall |
| `test_skill_persists_across_deactivate_reactivate` | Survives env cycle |
