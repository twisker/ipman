# CLI Passthrough & Symlink Guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `ipman skills`/`plugins` commands that transparently pass through to agent CLI, protect symlink integrity during agent operations, and fix skill listing to include workspace skills.

**Architecture:** Custom Click Group subclass (`AgentPassthroughGroup`) resolves known subcommands normally and falls back to a hidden passthrough handler for unknown ones. A `symlink_guard` context manager wraps all agent CLI calls to detect and auto-repair broken environment symlinks. OpenClaw adapter gains workspace `skills/` directory scanning as a fourth fallback strategy.

**Tech Stack:** Python 3.10+, Click, pathlib, shutil, pytest

**Spec:** `docs/superpowers/specs/2026-03-27-cli-passthrough-and-symlink-guard-design.md`

---

## File Structure

| Operation | File | Responsibility |
|-----------|------|----------------|
| Create | `src/ipman/cli/passthrough.py` | `AgentPassthroughGroup` class + `create_passthrough_group` factory |
| Modify | `src/ipman/cli/main.py` | Replace old `skill` group with `skills`/`plugins` groups + aliases |
| Modify | `src/ipman/cli/skill.py` | Extract `list_cmd` to be registered on new skills group |
| Modify | `src/ipman/core/environment.py` | Add `symlink_guard` + `_sync_and_restore_symlink` |
| Modify | `src/ipman/agents/openclaw.py` | Add `_scan_workspace_skills`, refactor `list_skills` |
| Create | `tests/test_cli/test_passthrough.py` | Unit tests for passthrough group |
| Create | `tests/test_core/test_symlink_guard.py` | Unit tests for symlink_guard |
| Modify | `tests/test_agents/test_adapters_cli.py` | Add workspace skills scan tests |
| Modify | `tests/e2e/test_openclaw_compat.py` | Add passthrough/plugins/alias e2e tests, fix xfail |

---

### Task 1: `symlink_guard` context manager

**Files:**
- Modify: `src/ipman/core/environment.py` (add after `deactivate_env` at ~line 276)
- Create: `tests/test_core/test_symlink_guard.py`

- [ ] **Step 1: Write failing tests for symlink_guard**

Create `tests/test_core/test_symlink_guard.py`:

```python
"""Tests for symlink_guard context manager."""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from ipman.core.environment import symlink_guard
from ipman.utils.symlink import create_symlink, is_symlink, resolve_symlink


def _setup_active_env(project: Path, env_name: str, agent_config_dir: str = ".openclaw") -> Path:
    """Create a fake active ipman environment with symlink."""
    # Create env directory
    env_path = project / ".ipman" / "envs" / env_name
    env_path.mkdir(parents=True)
    (env_path / "skills").mkdir()
    (env_path / "env.yaml").write_text(
        yaml.dump({"name": env_name, "agent": "openclaw"}),
    )

    # Create ipman.yaml config
    ipman_dir = project / ".ipman"
    ipman_dir.mkdir(exist_ok=True)
    (ipman_dir / "ipman.yaml").write_text(
        yaml.dump({
            "agent": "openclaw",
            "agent_config_dir": agent_config_dir,
            "active_env": env_name,
        }),
    )

    # Create symlink: .openclaw -> env_path
    link_path = project / agent_config_dir
    if link_path.exists():
        shutil.rmtree(link_path)
    create_symlink(target=env_path, link=link_path)

    return env_path


class TestSymlinkGuardNoOp:
    """Cases where symlink_guard should do nothing."""

    def test_no_active_env(self, tmp_path: Path) -> None:
        """No ipman.yaml → guard is a no-op."""
        with symlink_guard(tmp_path):
            pass  # should not raise

    def test_no_active_env_in_config(self, tmp_path: Path) -> None:
        """ipman.yaml exists but active_env is None → no-op."""
        ipman_dir = tmp_path / ".ipman"
        ipman_dir.mkdir()
        (ipman_dir / "ipman.yaml").write_text(
            yaml.dump({"agent": "openclaw", "agent_config_dir": ".openclaw", "active_env": None}),
        )
        with symlink_guard(tmp_path):
            pass

    def test_symlink_intact_after_operation(self, tmp_path: Path) -> None:
        """Symlink still valid after yield → no repair needed."""
        env_path = _setup_active_env(tmp_path, "test-env")
        link_path = tmp_path / ".openclaw"

        with symlink_guard(tmp_path):
            # Simulate agent writing a file (symlink stays intact)
            (link_path / "new_file.txt").write_text("hello")

        assert is_symlink(link_path)
        assert (env_path / "new_file.txt").exists()


class TestSymlinkGuardRepair:
    """Cases where symlink_guard should auto-repair."""

    def test_symlink_replaced_with_real_dir(self, tmp_path: Path) -> None:
        """Agent replaces symlink with real dir → sync and restore."""
        env_path = _setup_active_env(tmp_path, "test-env")
        link_path = tmp_path / ".openclaw"

        # Pre-existing file in env
        (env_path / "skills" / "old-skill").mkdir(parents=True)

        with symlink_guard(tmp_path):
            # Simulate agent destroying symlink and creating real dir
            target = resolve_symlink(link_path)
            link_path.unlink() if link_path.is_symlink() else shutil.rmtree(link_path)
            link_path.mkdir()
            # Agent writes new content
            (link_path / "plugins" / "new-ext").mkdir(parents=True)
            (link_path / "plugins" / "new-ext" / "manifest.json").write_text("{}")

        # Symlink should be restored
        assert is_symlink(link_path)
        # New content should be synced to env
        assert (env_path / "plugins" / "new-ext" / "manifest.json").exists()
        # Old content should still be there
        assert (env_path / "skills" / "old-skill").exists()

    def test_symlink_and_dir_both_gone(self, tmp_path: Path) -> None:
        """Both symlink and dir deleted → recreate symlink."""
        env_path = _setup_active_env(tmp_path, "test-env")
        link_path = tmp_path / ".openclaw"

        with symlink_guard(tmp_path):
            # Simulate agent deleting the symlink entirely
            link_path.unlink() if link_path.is_symlink() else shutil.rmtree(link_path)

        assert is_symlink(link_path)
        assert resolve_symlink(link_path) == env_path.resolve()

    def test_repair_failure_does_not_raise(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """If repair fails, warn but don't crash."""
        _setup_active_env(tmp_path, "test-env")
        link_path = tmp_path / ".openclaw"

        def _broken_create(*a, **kw):
            raise PermissionError("simulated")

        with symlink_guard(tmp_path):
            link_path.unlink() if link_path.is_symlink() else shutil.rmtree(link_path)
            # Monkey-patch create_symlink to fail during repair
            monkeypatch.setattr("ipman.core.environment.create_symlink", _broken_create)

        # Should not raise, just warn
        assert not is_symlink(link_path)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_core/test_symlink_guard.py -v`
Expected: FAIL — `symlink_guard` not yet defined.

- [ ] **Step 3: Implement `symlink_guard` and `_sync_and_restore_symlink`**

Add to `src/ipman/core/environment.py` after the `deactivate_env` function (after line 276):

```python
from contextlib import contextmanager


@contextmanager
def symlink_guard(project_path: Path | None = None):
    """Protect symlink integrity across agent CLI operations.

    Records the current symlink state before yield. After yield, checks
    if the symlink was broken and auto-repairs if needed.
    """
    project_path = project_path or Path.cwd()

    config = _read_project_config(project_path)
    if not config or not config.get("active_env"):
        yield
        return

    agent_config_dir = config.get("agent_config_dir", ".claude")
    link_path = project_path / agent_config_dir
    was_symlink = is_symlink(link_path)
    original_target = resolve_symlink(link_path) if was_symlink else None

    yield

    if not original_target or is_symlink(link_path):
        return  # nothing broken

    try:
        if link_path.exists():
            _sync_and_restore_symlink(link_path, original_target)
        else:
            create_symlink(target=original_target, link=link_path)
        import click
        click.secho(
            "\u26a0 Environment link was broken by agent CLI operation. Auto-repaired.",
            fg="yellow", err=True,
        )
    except Exception as exc:
        import click
        click.secho(
            f"\u26a0 Environment link was broken and auto-repair failed: {exc}\n"
            "  Run 'ipman env activate <name>' to manually restore.",
            fg="yellow", err=True,
        )


def _sync_and_restore_symlink(link_path: Path, original_target: Path) -> None:
    """Sync contents from a real dir back to env, then restore the symlink."""
    # Sync new/modified files to env directory
    shutil.copytree(link_path, original_target, dirs_exist_ok=True)
    # Remove the real directory
    shutil.rmtree(link_path)
    # Recreate symlink
    create_symlink(target=original_target, link=link_path)
```

Also add `contextmanager` to imports at the top and ensure `resolve_symlink` is imported from `ipman.utils.symlink`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_core/test_symlink_guard.py -v`
Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add src/ipman/core/environment.py tests/test_core/test_symlink_guard.py
git commit -m "feat: add symlink_guard context manager for env link protection"
```

---

### Task 2: OpenClaw workspace skills scanning (Strategy 4)

**Files:**
- Modify: `src/ipman/agents/openclaw.py:86-146`
- Modify: `tests/test_agents/test_adapters_cli.py` (add new test class after `TestOpenClawSkillListFallback`)

- [ ] **Step 1: Write failing tests for workspace skills scanning**

Add to `tests/test_agents/test_adapters_cli.py` after `TestOpenClawInstallFlags` class:

```python
class TestOpenClawWorkspaceSkillsScan:
    """Test Strategy 4: workspace skills/ directory scanning."""

    def setup_method(self) -> None:
        self.adapter = OpenClawAdapter()

    def test_scan_workspace_skills_found(self, tmp_path: Path) -> None:
        """Skills with SKILL.md in workspace/skills/ are discovered."""
        skills_dir = tmp_path / "skills"
        skill_a = skills_dir / "skill-a"
        skill_a.mkdir(parents=True)
        (skill_a / "SKILL.md").write_text("---\nname: skill-a\n---\n")

        skill_b = skills_dir / "skill-b"
        skill_b.mkdir()
        (skill_b / "SKILL.md").write_text("---\nname: skill-b\n---\n")

        result = self.adapter._scan_workspace_skills(tmp_path)
        names = {s.name for s in result}
        assert names == {"skill-a", "skill-b"}

    def test_scan_workspace_skills_empty(self, tmp_path: Path) -> None:
        """No skills/ directory → empty list."""
        result = self.adapter._scan_workspace_skills(tmp_path)
        assert result == []

    def test_scan_workspace_skills_no_skill_md(self, tmp_path: Path) -> None:
        """Directory without SKILL.md is skipped."""
        skills_dir = tmp_path / "skills"
        (skills_dir / "not-a-skill").mkdir(parents=True)
        (skills_dir / "not-a-skill" / "README.md").write_text("hello")

        result = self.adapter._scan_workspace_skills(tmp_path)
        assert result == []

    @patch("ipman.agents.openclaw.OpenClawAdapter._run_cli")
    def test_list_skills_merges_workspace(self, mock_run, tmp_path: Path) -> None:
        """list_skills merges clawhub results with workspace scan, deduped."""
        # clawhub list --json returns skill-a
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout='[{"name": "skill-a", "version": "1.0"}]',
            stderr="",
        )
        # workspace has skill-a (duplicate) and skill-b (new)
        skills_dir = tmp_path / "skills"
        for name in ("skill-a", "skill-b"):
            d = skills_dir / name
            d.mkdir(parents=True)
            (d / "SKILL.md").write_text(f"---\nname: {name}\n---\n")

        result = self.adapter.list_skills(workdir=tmp_path)
        names = [s.name for s in result]
        assert "skill-a" in names
        assert "skill-b" in names
        # skill-a should appear only once (clawhub version preferred)
        assert names.count("skill-a") == 1
        # clawhub version should have version info
        skill_a = next(s for s in result if s.name == "skill-a")
        assert skill_a.version == "1.0"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_agents/test_adapters_cli.py::TestOpenClawWorkspaceSkillsScan -v`
Expected: FAIL — `_scan_workspace_skills` not defined.

- [ ] **Step 3: Implement workspace skills scanning**

Modify `src/ipman/agents/openclaw.py`. Add `_scan_workspace_skills` static method and refactor `list_skills`:

```python
def list_skills(self, workdir: Path | None = None) -> list[SkillInfo]:
    """List installed skills with 4-strategy fallback.

    1. Try ``clawhub list --json``
    2. Fall back to parsing ``clawhub list`` plain text
    3. Fall back to reading ``.clawhub/lock.json``
    4. Merge workspace ``skills/`` directory scan
    """
    effective_workdir = workdir or Path.cwd()

    # Strategy 1: try --json
    result = self._run_cli(["clawhub", "list", "--json"])
    if result.returncode == 0:
        try:
            raw = json.loads(result.stdout)
            skills = [
                SkillInfo(
                    name=s.get("name", ""),
                    version=s.get("version", ""),
                )
                for s in raw
            ]
            return self._merge_workspace_skills(skills, effective_workdir)
        except (json.JSONDecodeError, TypeError):
            pass

    # Strategy 2: parse plain text
    result_plain = self._run_cli(["clawhub", "list"])
    if result_plain.returncode == 0 and result_plain.stdout.strip():
        skills = self._parse_plain_list(result_plain.stdout)
        return self._merge_workspace_skills(skills, effective_workdir)

    # Strategy 3: read lockfile
    skills = self._read_lockfile(effective_workdir)
    return self._merge_workspace_skills(skills, effective_workdir)

def _merge_workspace_skills(
    self, skills: list[SkillInfo], workdir: Path,
) -> list[SkillInfo]:
    """Merge workspace skills/ scan into existing results, deduped."""
    workspace_skills = self._scan_workspace_skills(workdir)
    known_names = {s.name for s in skills}
    for ws in workspace_skills:
        if ws.name not in known_names:
            skills.append(ws)
    return skills

@staticmethod
def _scan_workspace_skills(workdir: Path) -> list[SkillInfo]:
    """Scan workspace skills/ directory for locally installed skills."""
    skills_dir = workdir / "skills"
    if not skills_dir.exists():
        return []
    return [
        SkillInfo(name=entry.name, source="workspace")
        for entry in sorted(skills_dir.iterdir())
        if entry.is_dir() and (entry / "SKILL.md").exists()
    ]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_agents/test_adapters_cli.py::TestOpenClawWorkspaceSkillsScan -v`
Expected: All PASS.

Also run existing fallback tests to verify no regressions:
Run: `uv run pytest tests/test_agents/test_adapters_cli.py::TestOpenClawSkillListFallback -v`
Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add src/ipman/agents/openclaw.py tests/test_agents/test_adapters_cli.py
git commit -m "feat(openclaw): add workspace skills/ scanning as list_skills Strategy 4"
```

---

### Task 3: `AgentPassthroughGroup` class

**Files:**
- Create: `src/ipman/cli/passthrough.py`
- Create: `tests/test_cli/test_passthrough.py`

- [ ] **Step 1: Write failing tests for AgentPassthroughGroup**

Create `tests/test_cli/test_passthrough.py`:

```python
"""Tests for AgentPassthroughGroup."""
from __future__ import annotations

from unittest.mock import patch, MagicMock
import subprocess

import click
from click.testing import CliRunner

from ipman.cli.passthrough import create_passthrough_group


MOCK_CMD_MAP = {
    "openclaw": ["openclaw", "skills"],
    "claude-code": ["claude", "plugin"],
}


def _build_test_cli(agent_cmd_map: dict | None = None) -> click.Group:
    """Build a minimal CLI with a passthrough group for testing."""
    cmd_map = agent_cmd_map or MOCK_CMD_MAP

    @click.group()
    def cli():
        pass

    group = create_passthrough_group(
        name="skills",
        help="Manage skills.",
        agent_cmd_map=cmd_map,
    )

    # Register a known subcommand
    @group.command("list")
    def list_cmd():
        click.echo("known-list-output")

    cli.add_command(group, "skills")
    cli.add_command(group, "skill")  # alias
    return cli


class TestKnownSubcommand:
    """Known subcommands are dispatched normally."""

    def test_list_runs_normally(self) -> None:
        cli = _build_test_cli()
        runner = CliRunner()
        result = runner.invoke(cli, ["skills", "list"])
        assert result.exit_code == 0
        assert "known-list-output" in result.output

    def test_alias_skill_equals_skills(self) -> None:
        cli = _build_test_cli()
        runner = CliRunner()
        result = runner.invoke(cli, ["skill", "list"])
        assert result.exit_code == 0
        assert "known-list-output" in result.output


class TestUnknownSubcommandPassthrough:
    """Unknown subcommands are passed through to agent CLI."""

    @patch("ipman.cli.passthrough.resolve_agent")
    def test_unknown_cmd_passed_to_agent(self, mock_resolve) -> None:
        mock_adapter = MagicMock()
        mock_adapter.name = "openclaw"
        mock_adapter.display_name = "OpenClaw"
        mock_adapter._run_cli.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="agent-output\n", stderr="",
        )
        mock_resolve.return_value = mock_adapter

        cli = _build_test_cli()
        runner = CliRunner()
        result = runner.invoke(cli, ["skills", "enable", "my-skill"])
        assert result.exit_code == 0
        assert "agent-output" in result.output
        mock_adapter._run_cli.assert_called_once_with(
            ["openclaw", "skills", "enable", "my-skill"],
        )

    @patch("ipman.cli.passthrough.resolve_agent")
    def test_unknown_cmd_nonzero_exit(self, mock_resolve) -> None:
        mock_adapter = MagicMock()
        mock_adapter.name = "openclaw"
        mock_adapter.display_name = "OpenClaw"
        mock_adapter._run_cli.return_value = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="error msg\n",
        )
        mock_resolve.return_value = mock_adapter

        cli = _build_test_cli()
        runner = CliRunner()
        result = runner.invoke(cli, ["skills", "enable", "bad-skill"])
        assert result.exit_code == 1

    @patch("ipman.cli.passthrough.resolve_agent")
    def test_passthrough_with_agent_flag(self, mock_resolve) -> None:
        mock_adapter = MagicMock()
        mock_adapter.name = "claude-code"
        mock_adapter.display_name = "Claude Code"
        mock_adapter._run_cli.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="claude-out\n", stderr="",
        )
        mock_resolve.return_value = mock_adapter

        cli = _build_test_cli()
        runner = CliRunner()
        result = runner.invoke(cli, ["skills", "--agent", "claude-code", "enable", "x"])
        assert result.exit_code == 0
        mock_adapter._run_cli.assert_called_once_with(
            ["claude", "plugin", "enable", "x"],
        )


class TestHelpOutput:
    """Help includes both known commands and agent CLI reference."""

    def test_group_help_shows_known_commands(self) -> None:
        cli = _build_test_cli()
        runner = CliRunner()
        result = runner.invoke(cli, ["skills", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_cli/test_passthrough.py -v`
Expected: FAIL — `ipman.cli.passthrough` module not found.

- [ ] **Step 3: Implement `AgentPassthroughGroup`**

Create `src/ipman/cli/passthrough.py`:

```python
"""Passthrough Click group that delegates unknown subcommands to agent CLI."""
from __future__ import annotations

from pathlib import Path

import click

from ipman.cli._common import resolve_agent
from ipman.core.environment import symlink_guard


class AgentPassthroughGroup(click.Group):
    """Click group that passes unrecognized subcommands to agent CLI.

    Known subcommands (registered via @group.command) are handled
    normally. Unknown subcommands are forwarded to the agent's native
    CLI using the configured command prefix mapping.
    """

    def __init__(
        self,
        *args,
        agent_cmd_map: dict[str, list[str]],
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.agent_cmd_map = agent_cmd_map

    def resolve_command(self, ctx, args):
        """Try normal resolution first; fall back to passthrough."""
        cmd_name, cmd, remaining = super().resolve_command(ctx, args)
        if cmd is not None:
            return cmd_name, cmd, remaining
        # Unknown command → passthrough
        return "_passthrough", self.commands["_passthrough"], args

    def parse_args(self, ctx, args):
        """Extract --agent before normal parsing."""
        # Pull --agent from args if present (before subcommand parsing)
        agent_name = None
        filtered = []
        skip_next = False
        for i, arg in enumerate(args):
            if skip_next:
                skip_next = False
                continue
            if arg == "--agent" and i + 1 < len(args):
                agent_name = args[i + 1]
                skip_next = True
            elif arg.startswith("--agent="):
                agent_name = arg.split("=", 1)[1]
            else:
                filtered.append(arg)
        ctx.ensure_object(dict)
        ctx.obj["agent_name"] = agent_name
        return super().parse_args(ctx, filtered)

    def format_help(self, ctx, formatter):
        """Show ipman commands, then hint about agent passthrough."""
        super().format_help(ctx, formatter)
        formatter.write("\n")
        formatter.write(
            "  Unrecognized subcommands are passed through to the agent CLI.\n"
            "  Use --agent to specify the agent (or auto-detected).\n"
        )


def _make_passthrough_cmd(agent_cmd_map: dict[str, list[str]]) -> click.Command:
    """Create the hidden _passthrough command."""

    @click.command("_passthrough", hidden=True)
    @click.argument("args", nargs=-1, type=click.UNPROCESSED)
    @click.pass_context
    def _passthrough(ctx, args):
        agent_name = ctx.obj.get("agent_name") if ctx.obj else None
        adapter = resolve_agent(agent_name)

        prefix = agent_cmd_map.get(adapter.name)
        if not prefix:
            raise click.ClickException(
                f"Agent '{adapter.name}' is not supported by this command."
            )

        full_cmd = prefix + list(args)
        project_path = Path.cwd()

        with symlink_guard(project_path):
            result = adapter._run_cli(full_cmd)

        if result.stdout:
            click.echo(result.stdout, nl=False)
        if result.stderr:
            click.echo(result.stderr, nl=False, err=True)
        ctx.exit(result.returncode)

    return _passthrough


def create_passthrough_group(
    name: str,
    help: str,
    agent_cmd_map: dict[str, list[str]],
) -> AgentPassthroughGroup:
    """Factory: create a passthrough group with its hidden _passthrough command."""
    group = AgentPassthroughGroup(
        name=name,
        help=help,
        agent_cmd_map=agent_cmd_map,
    )
    group.add_command(_make_passthrough_cmd(agent_cmd_map))
    return group
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_cli/test_passthrough.py -v`
Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add src/ipman/cli/passthrough.py tests/test_cli/test_passthrough.py
git commit -m "feat: add AgentPassthroughGroup for CLI command passthrough"
```

---

### Task 4: Wire up `skills`/`plugins` groups in main CLI

**Files:**
- Modify: `src/ipman/cli/main.py`
- Modify: `src/ipman/cli/skill.py` (extract `list_cmd` registration)

- [ ] **Step 1: Write a smoke test for the new CLI structure**

Add to `tests/test_cli/test_passthrough.py`:

```python
class TestMainCLIIntegration:
    """Verify skills/plugins commands are registered on the real CLI."""

    def test_skills_command_exists(self) -> None:
        from ipman.cli.main import cli
        runner = CliRunner()
        result = runner.invoke(cli, ["skills", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output

    def test_skill_alias_exists(self) -> None:
        from ipman.cli.main import cli
        runner = CliRunner()
        result = runner.invoke(cli, ["skill", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output

    def test_plugins_command_exists(self) -> None:
        from ipman.cli.main import cli
        runner = CliRunner()
        result = runner.invoke(cli, ["plugins", "--help"])
        assert result.exit_code == 0

    def test_plugin_alias_exists(self) -> None:
        from ipman.cli.main import cli
        runner = CliRunner()
        result = runner.invoke(cli, ["plugin", "--help"])
        assert result.exit_code == 0

    def test_old_install_still_works(self) -> None:
        """Top-level install command is not broken."""
        from ipman.cli.main import cli
        runner = CliRunner()
        result = runner.invoke(cli, ["install", "--help"])
        assert result.exit_code == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cli/test_passthrough.py::TestMainCLIIntegration -v`
Expected: FAIL — `plugins` command not found.

- [ ] **Step 3: Modify `cli/main.py` to register new groups**

Replace the `skill` group registration in `src/ipman/cli/main.py`. The file currently reads:

```python
from ipman.cli.skill import install, skill, uninstall
# ...
cli.add_command(skill)
cli.add_command(install)
cli.add_command(uninstall)
```

Change to:

```python
from ipman.cli.skill import install, list_cmd, uninstall
from ipman.cli.passthrough import create_passthrough_group

SKILLS_CMD_MAP = {
    "claude-code": ["claude", "plugin"],
    "openclaw": ["openclaw", "skills"],
}

PLUGINS_CMD_MAP = {
    "claude-code": ["claude", "plugin"],
    "openclaw": ["openclaw", "plugins"],
}

# Create passthrough groups
skills_group = create_passthrough_group(
    name="skills",
    help="Manage skills in the current environment.",
    agent_cmd_map=SKILLS_CMD_MAP,
)
skills_group.add_command(list_cmd, "list")

plugins_group = create_passthrough_group(
    name="plugins",
    help="Manage plugins/extensions in the current environment.",
    agent_cmd_map=PLUGINS_CMD_MAP,
)

# Register groups + aliases
cli.add_command(skills_group, "skills")
cli.add_command(skills_group, "skill")
cli.add_command(plugins_group, "plugins")
cli.add_command(plugins_group, "plugin")

# Keep top-level install/uninstall (ipman's value-add commands)
cli.add_command(install)
cli.add_command(uninstall)
```

- [ ] **Step 4: Modify `cli/skill.py` to export `list_cmd` as standalone**

In `src/ipman/cli/skill.py`, the `list_cmd` function is currently registered under the old `skill` group via `@skill.command("list")`. Change it to a standalone Click command so it can be registered on the new group:

Replace the old `skill` group and `list_cmd`:

```python
# Remove the old @click.group skill() and @skill.command("list")
# Replace with a standalone command:

@click.command("list")
@click.option("--agent", "agent_name", default=None,
              help="Agent tool to use (e.g. claude-code, openclaw).")
def list_cmd(agent_name: str | None) -> None:
    """List installed skills via the agent's native CLI."""
    from ipman.core.environment import symlink_guard
    adapter = _resolve_agent(agent_name)
    with symlink_guard():
        skills = adapter.list_skills()
    if not skills:
        click.echo(f"No skills installed ({adapter.display_name}).")
        return
    for s in skills:
        status = "" if s.enabled else click.style(" (disabled)", fg="yellow")
        version = f" v{s.version}" if s.version else ""
        click.echo(f"  {s.name}{version}{status}")
    click.echo(f"\n{len(skills)} skill(s) installed.")
```

Keep the old `skill` group definition for now (but it won't be registered in main.py anymore). Or simply remove it — the `list_cmd` and `install`/`uninstall` are all that's needed.

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_cli/test_passthrough.py -v`
Expected: All PASS.

Also run existing CLI tests for regressions:
Run: `uv run pytest tests/test_cli/ -v`
Expected: All PASS (existing `test_skill.py` tests may need `skill` → `skills` adjustment if they invoke the group directly).

- [ ] **Step 6: Fix any existing test references to old `skill` group**

If `tests/test_cli/test_skill.py` invokes `["skill", "list"]`, it should still work because `skill` is an alias for `skills`. Verify and fix any failures.

- [ ] **Step 7: Commit**

```bash
git add src/ipman/cli/main.py src/ipman/cli/skill.py tests/test_cli/test_passthrough.py
git commit -m "feat: wire up skills/plugins passthrough groups with aliases"
```

---

### Task 5: E2E tests for passthrough, plugins, alias, and symlink repair

**Files:**
- Modify: `tests/e2e/test_openclaw_compat.py`
- Modify: `tests/e2e/conftest_mock.py` (may need mock openclaw script)

- [ ] **Step 1: Add mock openclaw script for passthrough testing**

Check if the existing mock clawhub covers `openclaw` commands. The current mock only handles `clawhub`. We need a mock `openclaw` script too.

Add to `tests/e2e/mock_clawhub/openclaw_mock.py`:

```python
#!/usr/bin/env python3
"""Mock openclaw CLI for e2e tests."""
import json
import sys

def main():
    args = sys.argv[1:]
    if not args:
        print("openclaw mock", file=sys.stderr)
        sys.exit(1)

    subcmd = args[0]

    if subcmd == "skills":
        handle_skills(args[1:])
    elif subcmd == "plugins":
        handle_plugins(args[1:])
    else:
        print(f"Unknown command: {subcmd}", file=sys.stderr)
        sys.exit(1)

def handle_skills(args):
    if not args:
        print("Usage: openclaw skills <command>")
        return
    cmd = args[0]
    if cmd == "list":
        print("mock-skill-a")
        print("mock-skill-b")
    elif cmd == "install":
        name = args[1] if len(args) > 1 else "unknown"
        print(f"Installed skill: {name}")
    elif cmd == "--help":
        print("openclaw skills: manage skills")
    else:
        print(f"openclaw skills {cmd}: OK")

def handle_plugins(args):
    if not args:
        print("Usage: openclaw plugins <command>")
        return
    cmd = args[0]
    if cmd == "list":
        print("mock-plugin-a")
    elif cmd == "install":
        name = args[1] if len(args) > 1 else "unknown"
        print(f"Installed plugin: {name}")
    elif cmd == "--help":
        print("openclaw plugins: manage plugins")
    else:
        print(f"openclaw plugins {cmd}: OK")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Register mock openclaw in conftest_mock.py**

Add a fixture to `tests/e2e/conftest_mock.py` that creates an `openclaw` wrapper (similar to the existing `clawhub` mock setup). Add inside the `mock_clawhub_env` fixture, after the clawhub wrapper creation:

```python
# Also create mock openclaw script
oc_mock_py = MOCK_CLAWHUB_DIR / "openclaw_mock.py"
oc_py_dest = mock_dir / "openclaw_mock.py"
shutil.copy2(oc_mock_py, oc_py_dest)

if sys.platform == "win32":
    oc_wrapper = mock_dir / "openclaw.cmd"
    oc_wrapper.write_text(
        f'@echo off\n"{python_exe}" "{oc_py_dest}" %*\n',
        encoding="utf-8",
    )
else:
    oc_wrapper = mock_dir / "openclaw"
    oc_wrapper.write_text(
        f'#!/usr/bin/env bash\nexec "{python_exe}" "{oc_py_dest}" "$@"\n',
        encoding="utf-8",
    )
    oc_wrapper.chmod(oc_wrapper.stat().st_mode | stat.S_IEXEC)
```

- [ ] **Step 3: Write e2e tests**

Add new test section to `tests/e2e/test_openclaw_compat.py`:

```python
# ===========================================================================
# Section 12: CLI passthrough, plugins, and alias tests
# ===========================================================================


class TestCLIPassthrough:
    """Verify skills/plugins passthrough to mock agent CLI."""

    def test_skills_passthrough_unknown_cmd(
        self, mock_openclaw_project: Path,
    ) -> None:
        """ipman skills <unknown> should passthrough to openclaw skills."""
        name = _unique_name()
        run_ipman("env", "create", name, "--agent", "openclaw",
                  cwd=mock_openclaw_project)
        run_ipman("env", "activate", name, cwd=mock_openclaw_project)

        result = run_ipman(
            "skills", "install", "test-skill",
            "--agent", "openclaw",
            cwd=mock_openclaw_project, check=False, timeout=30,
        )
        assert result.returncode == 0
        assert "test-skill" in result.stdout

        run_ipman("env", "deactivate",
                  cwd=mock_openclaw_project, check=False)
        run_ipman("env", "delete", name, "-y",
                  cwd=mock_openclaw_project, check=False)

    def test_plugins_passthrough(
        self, mock_openclaw_project: Path,
    ) -> None:
        """ipman plugins install should passthrough to openclaw plugins."""
        name = _unique_name()
        run_ipman("env", "create", name, "--agent", "openclaw",
                  cwd=mock_openclaw_project)
        run_ipman("env", "activate", name, cwd=mock_openclaw_project)

        result = run_ipman(
            "plugins", "install", "test-ext",
            "--agent", "openclaw",
            cwd=mock_openclaw_project, check=False, timeout=30,
        )
        assert result.returncode == 0
        assert "test-ext" in result.stdout

        run_ipman("env", "deactivate",
                  cwd=mock_openclaw_project, check=False)
        run_ipman("env", "delete", name, "-y",
                  cwd=mock_openclaw_project, check=False)

    def test_skill_alias_equals_skills(
        self, mock_openclaw_project: Path, mock_clawhub_env: Path,
    ) -> None:
        """ipman skill list should work as alias for ipman skills list."""
        name = _unique_name()
        run_ipman("env", "create", name, "--agent", "openclaw",
                  cwd=mock_openclaw_project)
        run_ipman("env", "activate", name, cwd=mock_openclaw_project)

        for sname in ("sk-x", "sk-y"):
            d = mock_clawhub_env / "skills" / sname
            d.mkdir(parents=True)

        r1 = run_ipman("skills", "list", "--agent", "openclaw",
                       cwd=mock_openclaw_project, check=False, timeout=30)
        r2 = run_ipman("skill", "list", "--agent", "openclaw",
                       cwd=mock_openclaw_project, check=False, timeout=30)
        assert r1.returncode == r2.returncode == 0
        # Both should list the same skills
        assert "sk-x" in r1.stdout
        assert "sk-x" in r2.stdout

        run_ipman("env", "deactivate",
                  cwd=mock_openclaw_project, check=False)
        run_ipman("env", "delete", name, "-y",
                  cwd=mock_openclaw_project, check=False)

    def test_skills_list_includes_workspace_skills(
        self, mock_openclaw_project: Path,
    ) -> None:
        """ipman skills list should include skills from workspace skills/ dir."""
        name = _unique_name()
        run_ipman("env", "create", name, "--agent", "openclaw",
                  cwd=mock_openclaw_project)
        run_ipman("env", "activate", name, cwd=mock_openclaw_project)

        # Create a workspace-level skill (not inside .openclaw)
        ws_skill = mock_openclaw_project / "skills" / "ws-skill"
        ws_skill.mkdir(parents=True)
        (ws_skill / "SKILL.md").write_text("---\nname: ws-skill\n---\nWorkspace skill")

        result = run_ipman(
            "skills", "list", "--agent", "openclaw",
            cwd=mock_openclaw_project, check=False, timeout=30,
        )
        assert result.returncode == 0
        assert "ws-skill" in result.stdout

        run_ipman("env", "deactivate",
                  cwd=mock_openclaw_project, check=False)
        run_ipman("env", "delete", name, "-y",
                  cwd=mock_openclaw_project, check=False)
```

- [ ] **Step 4: Update xfail test to expect pass**

In `tests/e2e/test_openclaw_compat.py`, class `TestSymlinkResilience`, method `test_env_survives_symlink_replacement`: remove the `pytest.xfail(...)` block and replace with:

```python
        # symlink_guard should have repaired during the operation
        # But this test simulates breakage OUTSIDE of symlink_guard,
        # so we verify that ipman env status still reads from ipman.yaml
        assert name in status.stdout, (
            f"Env '{name}' should still be shown as active via ipman.yaml config"
        )
```

Note: this test simulates breakage outside of `symlink_guard`. The actual fix for *this* test is that `get_env_status` / `list_envs` should also check `ipman.yaml`'s `active_env` field even when the symlink is broken. However, the primary fix path is `symlink_guard` preventing the breakage in the first place. Leave the xfail if this particular scenario isn't covered by symlink_guard — it will be a separate follow-up.

- [ ] **Step 5: Run all e2e tests**

Run: `uv run pytest tests/e2e/test_openclaw_compat.py -v --timeout=120`
Expected: All PASS (new tests) + existing tests still pass.

- [ ] **Step 6: Commit**

```bash
git add tests/e2e/ tests/e2e/mock_clawhub/openclaw_mock.py
git commit -m "test(e2e): add passthrough, plugins, alias, and workspace skills tests"
```

---

### Task 6: Full regression test and final cleanup

**Files:**
- All modified files from Tasks 1-5

- [ ] **Step 1: Run full unit test suite**

Run: `uv run pytest tests/test_core/ tests/test_cli/ tests/test_agents/ -v`
Expected: All PASS.

- [ ] **Step 2: Run full e2e test suite**

Run: `uv run pytest tests/e2e/ -v --timeout=120`
Expected: All PASS.

- [ ] **Step 3: Run linter and type checker**

Run: `uv run ruff check src/ipman/`
Run: `uv run mypy src/ipman/`
Expected: No errors.

- [ ] **Step 4: Fix any lint/type issues**

Address any issues found in step 3.

- [ ] **Step 5: Commit fixes if any**

```bash
git add -A
git commit -m "fix: lint and type check cleanup for passthrough feature"
```

- [ ] **Step 6: Update sprint and module docs**

Update `.claude/current-sprint.md` with the completed tasks.
Update `.claude/module-spec-registry.md` to add the new `cli/passthrough` module.

```bash
git add .claude/current-sprint.md .claude/module-spec-registry.md
git commit -m "docs: update sprint and module registry for CLI passthrough feature"
```
