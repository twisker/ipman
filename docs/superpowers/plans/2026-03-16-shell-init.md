# Shell Init Integration — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `ipman init` command that injects a shell function wrapper into the user's shell config, enabling `ipman env activate/deactivate` to work directly without manual `eval`.

**Architecture:** New `core/shell_init.py` handles injection content generation, config file reading/writing/backup, and marker-based block management. New `cli/init.py` provides the Click command. Existing `cli/env.py` activate/deactivate updated to show "Run ipman init" tip instead of eval hint.

**Tech Stack:** Python 3.10+, Click, pathlib

**Spec:** `docs/superpowers/specs/2026-03-16-shell-init-design.md`

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `src/ipman/core/shell_init.py` | Create | Shell detection, injection content generation, config file inject/remove/backup, is_initialized check |
| `src/ipman/cli/init.py` | Create | `ipman init` Click command (init, --reverse, --dry-run) |
| `src/ipman/cli/main.py:9,29` | Modify | Import and register `init` command |
| `src/ipman/cli/env.py:139-145,167-172` | Modify | Replace eval hint with "Run ipman init" tip |
| `tests/test_core/test_shell_init.py` | Create | 16 tests for core logic |
| `tests/test_cli/test_init.py` | Create | 5 tests for CLI command |

---

## Chunk 1: Core Logic + Tests

### Task 1: Create shell_init.py — constants and shell detection

**Files:**
- Create: `src/ipman/core/shell_init.py`
- Create: `tests/test_core/test_shell_init.py`

- [ ] **Step 1: Write failing tests for shell detection**

```python
# tests/test_core/test_shell_init.py
"""Tests for shell init integration."""

from __future__ import annotations

from pathlib import Path

import pytest

from ipman.core.shell_init import (
    MARKER_END,
    MARKER_START,
    config_file_path,
    detect_shell,
)


class TestDetectShell:

    def test_detect_bash(self, monkeypatch):
        monkeypatch.setenv("SHELL", "/bin/bash")
        monkeypatch.delenv("PSModulePath", raising=False)
        assert detect_shell() == "bash"

    def test_detect_zsh(self, monkeypatch):
        monkeypatch.setenv("SHELL", "/bin/zsh")
        monkeypatch.delenv("PSModulePath", raising=False)
        assert detect_shell() == "zsh"

    def test_detect_zsh_not_bash(self, monkeypatch):
        """zsh must be detected as zsh, not bash."""
        monkeypatch.setenv("SHELL", "/usr/bin/zsh")
        assert detect_shell() == "zsh"

    def test_detect_fish(self, monkeypatch):
        monkeypatch.setenv("SHELL", "/usr/bin/fish")
        assert detect_shell() == "fish"

    def test_detect_powershell(self, monkeypatch):
        monkeypatch.delenv("SHELL", raising=False)
        monkeypatch.setenv("PSModulePath", "C:\\something")
        assert detect_shell() == "powershell"

    def test_detect_fallback(self, monkeypatch):
        monkeypatch.delenv("SHELL", raising=False)
        monkeypatch.delenv("PSModulePath", raising=False)
        assert detect_shell() == "bash"


class TestConfigFilePath:

    def test_bash_path(self):
        p = config_file_path("bash")
        assert p == Path.home() / ".bashrc"

    def test_zsh_path(self):
        p = config_file_path("zsh")
        assert p == Path.home() / ".zshrc"

    def test_fish_path(self):
        p = config_file_path("fish")
        assert p == Path.home() / ".config" / "fish" / "config.fish"

    def test_powershell_path(self):
        p = config_file_path("powershell")
        assert "PowerShell" in str(p) or "powershell" in str(p).lower()

    def test_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown shell"):
            config_file_path("tcsh")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_core/test_shell_init.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement constants and detection**

```python
# src/ipman/core/shell_init.py
"""Shell init integration — inject/remove ipman wrapper in shell configs."""

from __future__ import annotations

import os
import sys
from pathlib import Path

MARKER_START = "# >>> ipman init >>>"
MARKER_END = "# <<< ipman init <<<"

SUPPORTED_SHELLS = ("bash", "zsh", "fish", "powershell")


def detect_shell() -> str:
    """Detect the current shell. Distinguishes zsh from bash."""
    shell_path = os.environ.get("SHELL", "")
    if "zsh" in shell_path:
        return "zsh"
    if "bash" in shell_path:
        return "bash"
    if "fish" in shell_path:
        return "fish"
    if os.environ.get("PSModulePath"):
        return "powershell"
    return "bash"


def config_file_path(shell: str) -> Path:
    """Return the config file path for the given shell."""
    if shell == "bash":
        return Path.home() / ".bashrc"
    if shell == "zsh":
        return Path.home() / ".zshrc"
    if shell == "fish":
        return Path.home() / ".config" / "fish" / "config.fish"
    if shell == "powershell":
        if sys.platform == "win32":
            docs = Path.home() / "Documents"
        else:
            docs = Path.home() / ".config"
        return docs / "PowerShell" / "Microsoft.PowerShell_profile.ps1"
    msg = f"Unknown shell: '{shell}'. Supported: {', '.join(SUPPORTED_SHELLS)}"
    raise ValueError(msg)
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_core/test_shell_init.py -v`
Expected: All pass.

- [ ] **Step 5: Commit**

```bash
git add src/ipman/core/shell_init.py tests/test_core/test_shell_init.py
git commit -m "feat: add shell detection and config file path resolution"
```

### Task 2: Injection content generation

**Files:**
- Modify: `src/ipman/core/shell_init.py`
- Modify: `tests/test_core/test_shell_init.py`

- [ ] **Step 1: Write failing tests for injection content**

Append to `tests/test_core/test_shell_init.py`:

```python
from ipman.core.shell_init import generate_injection


class TestGenerateInjection:

    def test_bash_has_markers(self):
        content = generate_injection("bash")
        assert content.startswith(MARKER_START)
        assert content.rstrip().endswith(MARKER_END)

    def test_bash_has_function(self):
        content = generate_injection("bash")
        assert "ipman()" in content
        assert 'command ipman' in content
        assert 'env activate' in content
        assert 'env deactivate' in content

    def test_zsh_same_as_bash(self):
        """zsh and bash use identical injection content."""
        assert generate_injection("zsh") == generate_injection("bash")

    def test_fish_has_function(self):
        content = generate_injection("fish")
        assert "function ipman" in content
        assert "command ipman" in content

    def test_powershell_has_function(self):
        content = generate_injection("powershell")
        assert "function ipman" in content
        assert "Get-Command ipman" in content
        assert "Invoke-Expression" in content
        assert "-join" in content  # multi-line join fix

    def test_unknown_shell_raises(self):
        with pytest.raises(ValueError):
            generate_injection("tcsh")
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_core/test_shell_init.py::TestGenerateInjection -v`

- [ ] **Step 3: Implement generate_injection()**

Add to `src/ipman/core/shell_init.py`:

```python
def generate_injection(shell: str) -> str:
    """Generate the shell function wrapper content with markers."""
    if shell in ("bash", "zsh"):
        return _bash_injection()
    if shell == "fish":
        return _fish_injection()
    if shell == "powershell":
        return _powershell_injection()
    msg = f"Unknown shell: '{shell}'. Supported: {', '.join(SUPPORTED_SHELLS)}"
    raise ValueError(msg)


def _bash_injection() -> str:
    return f"""{MARKER_START}
# !! Contents within this block are managed by 'ipman init' !!
ipman() {{
    if [ "$1" = "env" ] && [ "$2" = "activate" ]; then
        shift 2
        eval "$(command ipman env activate "$@")"
    elif [ "$1" = "env" ] && [ "$2" = "deactivate" ]; then
        shift 2
        eval "$(command ipman env deactivate "$@")"
    else
        command ipman "$@"
    fi
}}
{MARKER_END}
"""


def _fish_injection() -> str:
    return f"""{MARKER_START}
# !! Contents within this block are managed by 'ipman init' !!
function ipman
    if test "$argv[1]" = "env"; and test "$argv[2]" = "activate"
        eval (command ipman env activate $argv[3..])
    else if test "$argv[1]" = "env"; and test "$argv[2]" = "deactivate"
        eval (command ipman env deactivate $argv[3..])
    else
        command ipman $argv
    end
end
{MARKER_END}
"""


def _powershell_injection() -> str:
    return f"""{MARKER_START}
# !! Contents within this block are managed by 'ipman init' !!
function ipman {{
    $ipmanExe = (Get-Command ipman -CommandType Application).Source
    if ($args[0] -eq 'env' -and $args[1] -eq 'activate') {{
        $remaining = @($args | Select-Object -Skip 2)
        $script = (& $ipmanExe env activate @remaining) -join "`n"
        Invoke-Expression $script
    }} elseif ($args[0] -eq 'env' -and $args[1] -eq 'deactivate') {{
        $remaining = @($args | Select-Object -Skip 2)
        $script = (& $ipmanExe env deactivate @remaining) -join "`n"
        Invoke-Expression $script
    }} else {{
        & $ipmanExe @args
    }}
}}
{MARKER_END}
"""
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_core/test_shell_init.py -v`
Expected: All pass.

- [ ] **Step 5: Commit**

```bash
git add src/ipman/core/shell_init.py tests/test_core/test_shell_init.py
git commit -m "feat: add shell injection content generation for 4 shells"
```

### Task 3: Inject, remove, backup, and is_initialized

**Files:**
- Modify: `src/ipman/core/shell_init.py`
- Modify: `tests/test_core/test_shell_init.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_core/test_shell_init.py`:

```python
from ipman.core.shell_init import (
    inject_into_file,
    is_initialized,
    remove_from_file,
)


class TestInjectIntoFile:

    def test_inject_appends_to_file(self, tmp_path):
        cfg = tmp_path / ".bashrc"
        cfg.write_text("# existing content\n", encoding="utf-8")
        inject_into_file(cfg, "bash")
        content = cfg.read_text(encoding="utf-8")
        assert "# existing content" in content
        assert MARKER_START in content
        assert "ipman()" in content

    def test_inject_idempotent(self, tmp_path):
        cfg = tmp_path / ".bashrc"
        cfg.write_text("", encoding="utf-8")
        inject_into_file(cfg, "bash")
        inject_into_file(cfg, "bash")
        content = cfg.read_text(encoding="utf-8")
        assert content.count(MARKER_START) == 1

    def test_inject_upgrade(self, tmp_path):
        """Re-inject replaces old block with new content."""
        cfg = tmp_path / ".bashrc"
        cfg.write_text(f"before\n{MARKER_START}\nold stuff\n{MARKER_END}\nafter\n",
                       encoding="utf-8")
        inject_into_file(cfg, "bash")
        content = cfg.read_text(encoding="utf-8")
        assert "old stuff" not in content
        assert "ipman()" in content
        assert "before" in content
        assert "after" in content

    def test_inject_creates_file_if_missing(self, tmp_path):
        cfg = tmp_path / "subdir" / "config.fish"
        assert not cfg.exists()
        inject_into_file(cfg, "fish")
        assert cfg.exists()
        assert MARKER_START in cfg.read_text(encoding="utf-8")

    def test_backup_created(self, tmp_path):
        cfg = tmp_path / ".bashrc"
        cfg.write_text("original", encoding="utf-8")
        inject_into_file(cfg, "bash")
        backup = tmp_path / ".bashrc.ipman-backup"
        assert backup.exists()
        assert backup.read_text(encoding="utf-8") == "original"


class TestRemoveFromFile:

    def test_remove_injection(self, tmp_path):
        cfg = tmp_path / ".bashrc"
        cfg.write_text("", encoding="utf-8")
        inject_into_file(cfg, "bash")
        assert MARKER_START in cfg.read_text(encoding="utf-8")
        removed = remove_from_file(cfg)
        assert removed is True
        assert MARKER_START not in cfg.read_text(encoding="utf-8")

    def test_remove_not_present(self, tmp_path):
        cfg = tmp_path / ".bashrc"
        cfg.write_text("clean file\n", encoding="utf-8")
        removed = remove_from_file(cfg)
        assert removed is False
        assert cfg.read_text(encoding="utf-8") == "clean file\n"


class TestIsInitialized:

    def test_initialized_true(self, tmp_path):
        cfg = tmp_path / ".bashrc"
        cfg.write_text(f"stuff\n{MARKER_START}\nblock\n{MARKER_END}\n",
                       encoding="utf-8")
        assert is_initialized(cfg) is True

    def test_initialized_false(self, tmp_path):
        cfg = tmp_path / ".bashrc"
        cfg.write_text("no markers here\n", encoding="utf-8")
        assert is_initialized(cfg) is False

    def test_initialized_file_missing(self, tmp_path):
        cfg = tmp_path / ".bashrc"
        assert is_initialized(cfg) is False
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_core/test_shell_init.py::TestInjectIntoFile -v`

- [ ] **Step 3: Implement inject/remove/is_initialized**

Add to `src/ipman/core/shell_init.py`:

```python
def is_initialized(config_path: Path) -> bool:
    """Check if ipman init markers exist in the config file."""
    if not config_path.exists():
        return False
    content = config_path.read_text(encoding="utf-8")
    return MARKER_START in content and MARKER_END in content


def inject_into_file(config_path: Path, shell: str) -> None:
    """Inject the shell wrapper into a config file.

    - Creates file + parent dirs if missing
    - Creates .ipman-backup before modification
    - Idempotent: replaces existing block if present
    """
    # Ensure parent dirs exist
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Read existing content (or empty)
    if config_path.exists():
        content = config_path.read_text(encoding="utf-8")
        # Backup before modification
        backup_path = config_path.with_suffix(
            config_path.suffix + ".ipman-backup"
        )
        backup_path.write_text(content, encoding="utf-8")
    else:
        content = ""

    # Remove old block if present (idempotent upgrade)
    content = _strip_block(content)

    # Append new injection
    injection = generate_injection(shell)
    if content and not content.endswith("\n"):
        content += "\n"
    content += injection

    config_path.write_text(content, encoding="utf-8")


def remove_from_file(config_path: Path) -> bool:
    """Remove the ipman init block from a config file.

    Returns True if block was found and removed, False if not present.
    """
    if not config_path.exists():
        return False

    content = config_path.read_text(encoding="utf-8")
    if MARKER_START not in content:
        return False

    new_content = _strip_block(content)
    config_path.write_text(new_content, encoding="utf-8")
    return True


def _strip_block(content: str) -> str:
    """Remove the marker block from content string."""
    lines = content.splitlines(keepends=True)
    result: list[str] = []
    inside_block = False
    for line in lines:
        if line.rstrip() == MARKER_START:
            inside_block = True
            continue
        if line.rstrip() == MARKER_END:
            inside_block = False
            continue
        if not inside_block:
            result.append(line)
    return "".join(result)
```

- [ ] **Step 4: Run all tests**

Run: `uv run pytest tests/test_core/test_shell_init.py -v`
Expected: All 16 tests pass.

- [ ] **Step 5: Run full test suite**

Run: `uv run pytest tests/ --ignore=tests/e2e -v`
Expected: All pass.

- [ ] **Step 6: Commit**

```bash
git add src/ipman/core/shell_init.py tests/test_core/test_shell_init.py
git commit -m "feat: add inject/remove/backup/is_initialized for shell init"
```

---

## Chunk 2: CLI Command + env.py Integration

### Task 4: Create `ipman init` CLI command

**Files:**
- Create: `src/ipman/cli/init.py`
- Modify: `src/ipman/cli/main.py`
- Create: `tests/test_cli/test_init.py`

- [ ] **Step 1: Write failing CLI tests**

```python
# tests/test_cli/test_init.py
"""Tests for ipman init CLI command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from ipman.cli.main import cli


@patch("ipman.cli.init.config_file_path")
@patch("ipman.cli.init.detect_shell", return_value="bash")
class TestInitCommand:

    def test_init_default(self, mock_detect, mock_path, tmp_path):
        """ipman init auto-detects shell and injects."""
        cfg = tmp_path / ".bashrc"
        cfg.write_text("", encoding="utf-8")
        mock_path.return_value = cfg
        runner = CliRunner()
        result = runner.invoke(cli, ["init"])
        assert result.exit_code == 0
        assert "bash" in result.output.lower()
        assert "# >>> ipman init >>>" in cfg.read_text()

    def test_init_specific_shell(self, mock_detect, mock_path, tmp_path):
        """ipman init bash targets bash specifically."""
        cfg = tmp_path / ".bashrc"
        cfg.write_text("", encoding="utf-8")
        mock_path.return_value = cfg
        runner = CliRunner()
        result = runner.invoke(cli, ["init", "bash"])
        assert result.exit_code == 0
        assert "# >>> ipman init >>>" in cfg.read_text()

    def test_init_reverse(self, mock_detect, mock_path, tmp_path):
        """ipman init --reverse removes injection."""
        cfg = tmp_path / ".bashrc"
        cfg.write_text(
            "# >>> ipman init >>>\nstuff\n# <<< ipman init <<<\n",
            encoding="utf-8",
        )
        mock_path.return_value = cfg
        runner = CliRunner()
        result = runner.invoke(cli, ["init", "--reverse"])
        assert result.exit_code == 0
        assert "# >>> ipman init >>>" not in cfg.read_text()

    def test_init_dry_run(self, mock_detect, mock_path, tmp_path):
        """ipman init --dry-run prints but does not write."""
        cfg = tmp_path / ".bashrc"
        cfg.write_text("", encoding="utf-8")
        mock_path.return_value = cfg
        runner = CliRunner()
        result = runner.invoke(cli, ["init", "--dry-run"])
        assert result.exit_code == 0
        assert "ipman()" in result.output
        assert "# >>> ipman init >>>" not in cfg.read_text()

    def test_init_multiple_shells(self, mock_detect, mock_path, tmp_path):
        """ipman init bash zsh injects into both."""
        paths = {
            "bash": tmp_path / ".bashrc",
            "zsh": tmp_path / ".zshrc",
        }
        for p in paths.values():
            p.write_text("", encoding="utf-8")
        mock_path.side_effect = lambda s: paths[s]
        runner = CliRunner()
        result = runner.invoke(cli, ["init", "bash", "zsh"])
        assert result.exit_code == 0
        for p in paths.values():
            assert "# >>> ipman init >>>" in p.read_text()
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_cli/test_init.py -v`

- [ ] **Step 3: Create cli/init.py**

```python
# src/ipman/cli/init.py
"""CLI command for shell integration setup."""

from __future__ import annotations

import click

from ipman.core.shell_init import (
    SUPPORTED_SHELLS,
    config_file_path,
    detect_shell,
    generate_injection,
    inject_into_file,
    is_initialized,
    remove_from_file,
)


@click.command("init")
@click.argument("shells", nargs=-1)
@click.option("--reverse", is_flag=True, default=False,
              help="Remove ipman shell integration.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Print what would be injected without writing.")
def init(
    shells: tuple[str, ...],
    reverse: bool,
    dry_run: bool,
) -> None:
    """Set up shell integration for ipman.

    Injects a shell function wrapper so that 'ipman env activate'
    and 'ipman env deactivate' work directly without eval.

    \b
    Examples:
      ipman init            # auto-detect shell
      ipman init bash zsh   # target specific shells
      ipman init --reverse  # remove integration
      ipman init --dry-run  # preview without writing
    """
    if not shells:
        shells = (detect_shell(),)

    for shell in shells:
        if shell not in SUPPORTED_SHELLS:
            click.secho(
                f"Unknown shell: '{shell}'. "
                f"Supported: {', '.join(SUPPORTED_SHELLS)}",
                fg="red", err=True,
            )
            continue

        cfg = config_file_path(shell)

        if dry_run:
            click.echo(f"Shell: {shell}")
            click.echo(f"Config: {cfg}")
            click.echo("Would inject:")
            click.echo(generate_injection(shell))
            continue

        if reverse:
            removed = remove_from_file(cfg)
            if removed:
                click.secho(
                    f"Removed ipman shell integration from {cfg}",
                    fg="green",
                )
                click.echo(f"Restart your shell or run:\n  source {cfg}")
            else:
                click.echo(
                    f"ipman init has not been run for {shell} ({cfg})"
                )
            continue

        # Normal inject
        inject_into_file(cfg, shell)
        click.secho(f"Detected shell: {shell}", fg="green")
        click.secho(f"Modified: {cfg}", fg="green")
        click.echo(
            "Shell integration installed. Restart your shell or run:\n"
            f"  source {cfg}"
        )
```

- [ ] **Step 4: Register in main.py**

Add to `src/ipman/cli/main.py`:

Import: `from ipman.cli.init import init`
Register: `cli.add_command(init)`

- [ ] **Step 5: Run CLI tests**

Run: `uv run pytest tests/test_cli/test_init.py -v`
Expected: All 5 pass.

- [ ] **Step 6: Verify ipman init --help works**

Run: `uv run ipman init --help`
Expected: Shows usage with shells argument and --reverse/--dry-run options.

- [ ] **Step 7: Commit**

```bash
git add src/ipman/cli/init.py src/ipman/cli/main.py tests/test_cli/test_init.py
git commit -m "feat: add ipman init CLI command for shell integration"
```

### Task 5: Update env.py activate/deactivate messaging

**Files:**
- Modify: `src/ipman/cli/env.py:139-145,167-172`

- [ ] **Step 1: Update activate command**

Replace the TTY block in `activate()` (lines 139-145):

```python
        if os.isatty(1):
            click.secho(f"Activated '{name}'.", fg="green")
            click.echo(f"  Prompt tag: {prompt_tag}")
            from ipman.core.shell_init import (
                config_file_path,
                detect_shell,
                is_initialized,
            )
            detected = detect_shell()
            try:
                initialized = is_initialized(config_file_path(detected))
            except ValueError:
                initialized = False
            if not initialized:
                click.echo(
                    "\nTip: Run 'ipman init' to enable automatic "
                    "shell integration.\n"
                    "     After that, 'ipman env activate' will "
                    "update your prompt directly."
                )
```

- [ ] **Step 2: Update deactivate command**

Replace the TTY block in `deactivate()` (lines 167-172):

```python
        if os.isatty(1):
            click.secho("Environment deactivated.", fg="green")
            from ipman.core.shell_init import (
                config_file_path,
                detect_shell,
                is_initialized,
            )
            detected = detect_shell()
            try:
                initialized = is_initialized(config_file_path(detected))
            except ValueError:
                initialized = False
            if not initialized:
                click.echo(
                    "\nTip: Run 'ipman init' to enable automatic "
                    "shell integration."
                )
```

- [ ] **Step 3: Update docstrings**

Change the activate docstring from:

```
    To update your shell prompt, use:
        eval "$(ipman env activate myenv)"
```

To:

```
    Run 'ipman init' first for automatic shell integration.
```

Same for deactivate.

- [ ] **Step 4: Run existing env CLI tests**

Run: `uv run pytest tests/test_cli/test_env.py -v`
Expected: All pass (tests use CliRunner which captures output, not a real TTY).

- [ ] **Step 5: Run full test suite**

Run: `uv run pytest tests/ --ignore=tests/e2e -v`
Expected: All pass.

- [ ] **Step 6: Commit**

```bash
git add src/ipman/cli/env.py
git commit -m "feat: replace eval hint with 'ipman init' tip in activate/deactivate"
```

### Task 6: Final verification

- [ ] **Step 1: Run full test suite**

Run: `uv run pytest tests/ --ignore=tests/e2e -v`
Expected: All pass.

- [ ] **Step 2: Lint and type check**

Run: `uv run ruff check src/ tests/ && uv run mypy src/`
Expected: Clean.

- [ ] **Step 3: Manual smoke test**

```bash
uv run ipman init --dry-run
# Should print bash injection content

uv run ipman init --help
# Should show usage

uv run ipman env activate --help
# Docstring should mention ipman init, not eval
```

- [ ] **Step 4: Commit any fixes**

```bash
git add -u
git commit -m "fix: address linting/type issues from shell init feature"
```
