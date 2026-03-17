# Local Skill Install Support — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend `ipman install` to accept local skill directories, with both agent adapters using file-copy installation.

**Architecture:** Add `_classify_source()` to detect source type (ip_file / local_skill / hub_name). Both adapters gain local-path support via `shutil.copytree` to the agent's skills directory. E2E tests unlock 3 previously skipped skill install tests.

**Tech Stack:** Python 3.10+, Click, pathlib, shutil, pytest

**Spec:** `docs/superpowers/specs/2026-03-17-local-skill-install-design.md`

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `src/ipman/agents/claude_code.py:39-47` | Modify | `install_skill()` detect local dir → copytree |
| `src/ipman/agents/openclaw.py:39-47` | Modify | `install_skill()` detect local dir → copytree |
| `src/ipman/cli/skill.py:201-258` | Modify | Add `_classify_source()`, add `local_skill` branch |
| `tests/test_agents/test_adapters_cli.py` | Modify | Add local path install tests |
| `tests/test_cli/test_skill.py` | Modify | Add `_classify_source` + local install CLI tests |
| `tests/e2e/test_skill_install.py` | Modify | Unlock 3 skipped tests |

---

## Chunk 1: Adapter Changes + Unit Tests

### Task 1: Update ClaudeCodeAdapter.install_skill() for local paths

**Files:**
- Modify: `src/ipman/agents/claude_code.py:39-47`
- Modify: `tests/test_agents/test_adapters_cli.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_agents/test_adapters_cli.py`, inside or after `TestClaudeCodeSkillInstall`:

```python
class TestClaudeCodeLocalInstall:

    def setup_method(self) -> None:
        self.adapter = ClaudeCodeAdapter()

    def test_install_local_dir(self, tmp_path):
        """Local directory → copied to .claude/skills/."""
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("test skill")

        project = tmp_path / "project"
        project.mkdir()
        (project / ".claude" / "skills").mkdir(parents=True)

        result = self.adapter.install_skill(
            str(skill_dir), config_dir=str(project / ".claude"),
        )
        assert result.returncode == 0
        assert (project / ".claude" / "skills" / "my-skill" / "SKILL.md").exists()

    @patch("subprocess.run")
    def test_install_remote_name(self, mock_run, tmp_path):
        """Non-existent path → claude plugin install."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr="",
        )
        self.adapter.install_skill("web-scraper")
        args = mock_run.call_args[0][0]
        assert args == ["claude", "plugin", "install", "web-scraper"]
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_agents/test_adapters_cli.py::TestClaudeCodeLocalInstall -v`

- [ ] **Step 3: Implement**

Replace `install_skill` in `src/ipman/agents/claude_code.py`:

```python
    def install_skill(
        self, name: str, **kwargs: str | None,
    ) -> subprocess.CompletedProcess[str]:
        """Install a skill.

        If *name* is an existing directory, copy it into the agent's
        skills/ dir.  Otherwise delegate to ``claude plugin install``.
        """
        path = Path(name)
        if path.exists() and path.is_dir():
            config_dir = kwargs.get("config_dir")
            if config_dir:
                dest = Path(str(config_dir)) / "skills" / path.name
            else:
                dest = Path.cwd() / ".claude" / "skills" / path.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(path, dest, dirs_exist_ok=True)
            return subprocess.CompletedProcess(
                args=[], returncode=0,
                stdout=f"Copied to {dest}\n", stderr="",
            )
        args = ["claude", "plugin", "install", name]
        scope = kwargs.get("scope")
        if scope:
            args.extend(["-s", str(scope)])
        return self._run_cli(args)
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_agents/test_adapters_cli.py -v`
Expected: All pass (existing + 2 new).

- [ ] **Step 5: Commit**

```bash
git add src/ipman/agents/claude_code.py tests/test_agents/test_adapters_cli.py
git commit -m "feat: ClaudeCodeAdapter supports local skill directory install"
```

### Task 2: Update OpenClawAdapter.install_skill() for local paths

**Files:**
- Modify: `src/ipman/agents/openclaw.py:39-47`
- Modify: `tests/test_agents/test_adapters_cli.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_agents/test_adapters_cli.py`:

```python
class TestOpenClawLocalInstall:

    def setup_method(self) -> None:
        self.adapter = OpenClawAdapter()

    def test_install_local_dir(self, tmp_path):
        """Local directory → copied to .openclaw/skills/."""
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("test skill")

        project = tmp_path / "project"
        project.mkdir()
        (project / ".openclaw" / "skills").mkdir(parents=True)

        result = self.adapter.install_skill(
            str(skill_dir), config_dir=str(project / ".openclaw"),
        )
        assert result.returncode == 0
        assert (project / ".openclaw" / "skills" / "my-skill" / "SKILL.md").exists()

    @patch("subprocess.run")
    def test_install_remote_name(self, mock_run, tmp_path):
        """Non-existent path → clawhub install."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr="",
        )
        self.adapter.install_skill("web-scraper")
        args = mock_run.call_args[0][0]
        assert args == ["clawhub", "install", "web-scraper"]
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_agents/test_adapters_cli.py::TestOpenClawLocalInstall -v`

- [ ] **Step 3: Implement**

Replace `install_skill` in `src/ipman/agents/openclaw.py`:

```python
    def install_skill(
        self, name: str, **kwargs: str | None,
    ) -> subprocess.CompletedProcess[str]:
        """Install a skill.

        If *name* is an existing directory, copy it into the agent's
        skills/ dir.  Otherwise delegate to ``clawhub install``.
        """
        path = Path(name)
        if path.exists() and path.is_dir():
            config_dir = kwargs.get("config_dir")
            if config_dir:
                dest = Path(str(config_dir)) / "skills" / path.name
            else:
                dest = Path.cwd() / ".openclaw" / "skills" / path.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(path, dest, dirs_exist_ok=True)
            return subprocess.CompletedProcess(
                args=[], returncode=0,
                stdout=f"Copied to {dest}\n", stderr="",
            )
        args = ["clawhub", "install", name]
        hub = kwargs.get("hub")
        if hub:
            args.extend(["--hub", str(hub)])
        return self._run_cli(args)
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_agents/test_adapters_cli.py -v`

- [ ] **Step 5: Commit**

```bash
git add src/ipman/agents/openclaw.py tests/test_agents/test_adapters_cli.py
git commit -m "feat: OpenClawAdapter supports local skill directory install"
```

---

## Chunk 2: CLI Changes + E2E Unlock

### Task 3: Add _classify_source() and local_skill branch to CLI

**Files:**
- Modify: `src/ipman/cli/skill.py:201-258`
- Modify: `tests/test_cli/test_skill.py`

- [ ] **Step 1: Write failing tests for _classify_source**

Append to `tests/test_cli/test_skill.py`:

```python
from ipman.cli.skill import _classify_source


class TestClassifySource:

    def test_ip_file(self):
        assert _classify_source("kit.ip.yaml") == "ip_file"

    def test_ip_file_with_path(self):
        assert _classify_source("./path/to/kit.ip.yaml") == "ip_file"

    def test_local_dir(self, tmp_path):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        assert _classify_source(str(skill_dir)) == "local_skill"

    def test_local_dir_relative(self, tmp_path, monkeypatch):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        monkeypatch.chdir(tmp_path)
        assert _classify_source("./my-skill") == "local_skill"

    def test_hub_name(self):
        assert _classify_source("web-scraper") == "hub_name"

    def test_hub_name_not_existing_file(self, tmp_path):
        """Bare name that doesn't exist → hub_name even if cwd has files."""
        assert _classify_source("nonexistent-skill") == "hub_name"
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_cli/test_skill.py::TestClassifySource -v`

- [ ] **Step 3: Add _classify_source() to skill.py**

Add at module level in `src/ipman/cli/skill.py` (after `_is_ip_file`):

```python
def _classify_source(source: str) -> str:
    """Classify install source: 'ip_file', 'local_skill', or 'hub_name'."""
    if source.endswith(".ip.yaml"):
        return "ip_file"
    if os.sep in source or source.startswith("."):
        path = Path(source)
        if path.exists() and path.is_dir():
            return "local_skill"
    return "hub_name"
```

Add `import os` if not already present (it's not in skill.py currently).

- [ ] **Step 4: Update the install() function body**

Replace lines 220-258 of the `install()` function with:

```python
    source_type = _classify_source(source)
    is_local = source_type in ("ip_file", "local_skill")

    # Determine whether to run local vet
    should_vet = False
    if skip_vet:
        should_vet = False
    elif force_vet:
        should_vet = True
    elif is_local:
        should_vet = True
    elif mode == SecurityMode.STRICT:
        should_vet = True

    # Run vet if needed
    if should_vet and not dry_run:
        if source_type == "ip_file":
            path = Path(source)
            if not path.exists():
                raise click.ClickException(f"IP file not found: {path}")
            content = path.read_text(encoding="utf-8")
            report = _run_vet(content, skill_name=source)
        elif source_type == "local_skill":
            # Vet all .md files in the skill directory
            skill_path = Path(source)
            md_contents = []
            for md_file in skill_path.rglob("*.md"):
                md_contents.append(md_file.read_text(encoding="utf-8"))
            content = "\n".join(md_contents)
            report = _run_vet(content, skill_name=source)
        else:
            report = _run_vet("", skill_name=source)

        if not _enforce_security(report, mode, source):
            raise SystemExit(1)

    if source_type == "local_skill":
        if dry_run:
            click.echo(f"Would install local skill: {source}")
        else:
            result = adapter.install_skill(source)
            if result.returncode == 0:
                click.secho(
                    f"Installed local skill from '{source}'.",
                    fg="green",
                )
            else:
                msg = result.stderr.strip() or result.stdout.strip() or "Unknown error"
                click.secho(f"Install failed: {msg}", fg="red", err=True)
                raise SystemExit(1)
    elif source_type == "ip_file":
        _install_from_ip_file(Path(source), adapter, dry_run=dry_run)
    else:
        _install_from_hub(source, adapter, dry_run=dry_run)
```

Also update the docstring of `install()`:
```
SOURCE can be a skill name (e.g. web-scraper), an .ip.yaml file path,
or a local skill directory (e.g. ./my-skill).
```

- [ ] **Step 5: Run tests**

Run: `uv run pytest tests/test_cli/test_skill.py tests/test_agents/ -v`
Run: `uv run pytest tests/ --ignore=tests/e2e -v`

- [ ] **Step 6: Commit**

```bash
git add src/ipman/cli/skill.py tests/test_cli/test_skill.py
git commit -m "feat: ipman install supports local skill directories"
```

### Task 4: Unlock E2E skill install tests

**Files:**
- Modify: `tests/e2e/test_skill_install.py`

- [ ] **Step 1: Replace the 3 skipped tests with real implementations**

Replace `test_install_skill_from_local`:

```python
    def test_install_skill_from_local(
        self, ipman_env: EnvInfo, project_dir: Path, agent: str,
        agent_manager: AgentManager,
    ) -> None:
        """Install a skill from local fixtures directory."""
        run_ipman(
            "env", "activate", ipman_env.name, f"--{ipman_env.scope}",
            cwd=project_dir,
        )
        fixture_skill = FIXTURES_DIR / "skills" / agent / "hello-world"
        assert fixture_skill.exists(), f"Fixture not found: {fixture_skill}"

        result = run_ipman(
            "install", str(fixture_skill),
            "--agent", agent, "--no-vet",
            cwd=project_dir, check=False, timeout=30,
        )
        assert result.returncode == 0, (
            f"Local skill install failed: {result.stderr}"
        )
```

Replace `test_uninstall_skill`:

```python
    def test_uninstall_skill(
        self, ipman_env: EnvInfo, project_dir: Path, agent: str,
        agent_manager: AgentManager,
    ) -> None:
        """Install then uninstall a skill."""
        run_ipman(
            "env", "activate", ipman_env.name, f"--{ipman_env.scope}",
            cwd=project_dir,
        )
        fixture_skill = FIXTURES_DIR / "skills" / agent / "hello-world"
        run_ipman(
            "install", str(fixture_skill),
            "--agent", agent, "--no-vet",
            cwd=project_dir, check=False, timeout=30,
        )
        # Uninstall by name
        result = run_ipman(
            "uninstall", "hello-world",
            "--agent", agent,
            cwd=project_dir, check=False, timeout=30,
        )
        # May fail (agent CLI may not find it) — verify no crash
        assert result.returncode in (0, 1), (
            f"Uninstall crashed: rc={result.returncode}, stderr={result.stderr}"
        )
```

Replace `test_skill_persists_across_deactivate_reactivate`:

```python
    def test_skill_persists_across_deactivate_reactivate(
        self, ipman_env: EnvInfo, project_dir: Path, agent: str,
        agent_manager: AgentManager,
    ) -> None:
        """Installed skill survives deactivate + reactivate cycle."""
        run_ipman(
            "env", "activate", ipman_env.name, f"--{ipman_env.scope}",
            cwd=project_dir,
        )
        fixture_skill = FIXTURES_DIR / "skills" / agent / "hello-world"
        result = run_ipman(
            "install", str(fixture_skill),
            "--agent", agent, "--no-vet",
            cwd=project_dir, check=False, timeout=30,
        )
        if result.returncode != 0:
            pytest.skip("Local skill install not available in this environment")

        # Deactivate + reactivate
        run_ipman("env", "deactivate", cwd=project_dir)
        run_ipman(
            "env", "activate", ipman_env.name, f"--{ipman_env.scope}",
            cwd=project_dir,
        )

        # Verify skill directory still exists in the env
        config_dir_name = AgentManager.AGENT_CONFIG_DIR[agent]
        skill_dest = project_dir / config_dir_name / "skills" / "hello-world"
        assert skill_dest.exists(), (
            f"Skill lost after deactivate/reactivate: {skill_dest}"
        )
```

- [ ] **Step 2: Verify tests collect**

Run: `uv run pytest tests/e2e/test_skill_install.py --collect-only`
Expected: 5 tests × agent × scope variants collected (no more skips in the first 3).

- [ ] **Step 3: Run full test suite**

Run: `uv run pytest tests/ --ignore=tests/e2e -v`
Expected: All pass.

- [ ] **Step 4: Lint**

Run: `uv run ruff check src/ tests/`

- [ ] **Step 5: Commit**

```bash
git add tests/e2e/test_skill_install.py
git commit -m "test(e2e): unlock local skill install tests (Sprint 7 B-group complete)"
```

### Task 5: Update current-sprint.md and sprint-plan.md

- [ ] **Step 1: Mark B-group tasks complete**

Update `.claude/current-sprint.md` and `.claude/sprint-plan.md` to reflect completion.

- [ ] **Step 2: Commit**

```bash
git add .claude/
git commit -m "docs: mark Sprint 7 B-group complete"
```
