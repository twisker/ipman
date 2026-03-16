# Cross-Platform E2E Testing Framework Design

> IpMan - Intelligence Package Manager
> Date: 2026-03-16
> Status: Approved

## 1. Background & Motivation

IpMan has reached v0.1.88 with all 6 development phases complete. While unit tests (68+) pass across 3 OS × 4 Python versions, real-world usage reveals critical bugs that mocked tests cannot catch:

- **Windows symlink overwrite**: Claude Code replaces `.claude` symlinks/junctions with physical directories during runtime, breaking ipman's virtual environment mechanism.
- **Publish workflow failures**: GitHub permission issues, webhook problems, and fork/PR edge cases cause frequent publish interruptions.
- **Init order fragility**: Creating ipman environments before vs. after an agent has been initialized may produce inconsistent results.

These issues exist at the boundary between ipman, real agent runtimes, and real operating systems — a boundary that current tests (unit mocks + Docker-only E2E bash scripts) do not cover.

## 2. Goals

1. **Real agent integration**: Test with actually installed Claude Code and OpenClaw (not mocks), including real agent sessions.
2. **Three-platform coverage**: Run on native Windows, Linux, and macOS (not emulated via Docker).
3. **All scopes**: Test every agent × scope combination (Claude Code: project/user/machine; OpenClaw: workspace/local/managed).
4. **Publish security**: Validate cross-account isolation with anonymous, owner, and multiple authenticated GitHub identities.
5. **Init order independence**: Verify ipman-first and agent-first initialization paths produce equivalent outcomes.
6. **Controllable, repeatable, observable**: Automated via CI/CD, with standard pytest reporting (JUnit XML).
7. **Extensible**: Adding a new agent requires only config entries and fixture data, zero test code changes.

## 3. Constraints

- **Budget**: $0 — public repository, GitHub Actions free for public repos.
- **Infrastructure**: GitHub Actions standard runners (ubuntu-latest, macos-latest, windows-latest).
- **Secrets**: ANTHROPIC_API_KEY, three GitHub PATs (owner, user_a, user_b) configured in repo secrets.
- **Agent sessions**: Real but minimal — short prompts like "Reply with exactly: OK" to minimize API cost and latency.
- **Test framework**: pytest (already used for 68+ unit tests in the project).

## 4. Test Architecture

### 4.1 Layered Strategy

```
+-----------------------------------------------------+
|  Layer 3: Agent Session Tests                       |
|  Real agent starts a short session; verify env      |
|  integrity (symlinks, skills, metadata).            |
|  Frequency: daily + release    Duration: ~10 min    |
+-----------------------------------------------------+
|  Layer 2: Agent CLI Integration Tests               |
|  Real agent CLI commands (install/uninstall/list).   |
|  Frequency: every push        Duration: ~5 min      |
+-----------------------------------------------------+
|  Layer 1: Platform Integration Tests                |
|  ipman's own cross-platform behavior (symlink, env, |
|  pack, publish).                                    |
|  Frequency: every push        Duration: ~3 min      |
+-----------------------------------------------------+
|  Layer 0: Unit Tests (existing, unchanged)          |
|  68+ pytest tests with mocked dependencies.         |
|  Frequency: every push        Duration: ~30 sec     |
+-----------------------------------------------------+
```

### 4.2 Directory Structure

```
tests/
  e2e/
    conftest.py                    # Core fixtures
    markers.py                     # Custom marker registration

    # Layer 1: Platform Integration
    test_env_lifecycle.py          # Environment CRUD across scopes
    test_symlink_integrity.py      # Cross-platform symlink/junction behavior
    test_pack_roundtrip.py         # pack -> .ip.yaml -> install roundtrip
    test_publish_workflow.py       # Publish + cross-account security matrix
    test_init_order.py             # Agent/ipman initialization order independence

    # Layer 2: Agent CLI Integration
    test_skill_install.py          # Real agent CLI skill install/uninstall
    test_ip_install.py             # IP package install (local + hub)

    # Layer 3: Agent Session
    test_agent_session.py          # Real agent session, verify env integrity

    fixtures/
      skills/
        claude-code/
          hello-world/             # Minimal Claude Code skill
        openclaw/
          hello-world/             # Minimal OpenClaw skill
      ips/
        clean-kit.ip.yaml          # Clean IP package
        with-deps.ip.yaml          # IP package with dependencies

    helpers/
      agent_manager.py             # Agent install/detect/session management
      platform_utils.py            # Cross-platform assertions (symlink, junction)
      github_cleanup.py            # Post-publish GitHub cleanup
```

### 4.3 CI Matrix

```
OS:    [ubuntu-latest, macos-latest, windows-latest]
Agent: [claude-code, openclaw]
Scope: parametrized inside pytest (project, user, machine / workspace, local, managed)
```

Full matrix: OS(3) x Agent(2) = 6 CI jobs. Scope(3) x Order(2) parametrized within pytest, yielding up to 36 logical combinations per test function.

### 4.4 pytest Markers

| Marker                    | Description                       | Default Run        |
|---------------------------|-----------------------------------|-------------------|
| `@pytest.mark.e2e`        | All E2E tests                     | CI only           |
| `@pytest.mark.platform`   | Layer 1 platform integration      | Every push        |
| `@pytest.mark.agent_cli`  | Layer 2 agent CLI                 | Every push        |
| `@pytest.mark.agent_session` | Layer 3 agent session          | Daily + release   |
| `@pytest.mark.publish`    | Publish workflow tests            | Daily + release   |
| `@pytest.mark.symlink`    | Symlink-specific tests            | Every push        |
| `@pytest.mark.slow`       | Tests taking > 30s                | Daily + release   |

## 5. Core Fixtures

### 5.1 Agent & Scope Parametrization

```python
AGENT_SCOPES = {
    "claude-code": {
        "project":  "project",
        "user":     "user",
        "machine":  "machine",
    },
    "openclaw": {
        "workspace": "project",
        "local":     "user",
        "managed":   "machine",
    },
}

@pytest.fixture(params=["claude-code", "openclaw"])
def agent(request):
    name = request.param
    if not AgentManager.is_installed(name):
        pytest.skip(f"{name} not installed")
    return name

@pytest.fixture(params=["project", "user", "machine"])
def scope(request, agent):
    s = request.param
    if s not in AGENT_SCOPES.get(agent, {}):
        pytest.skip(f"{agent} does not support scope '{s}'")
    if s == "machine" and not _has_machine_scope_permission():
        pytest.skip("machine scope requires elevated permissions")
    return s
```

### 5.2 Project Environment

```python
@pytest.fixture
def project_dir(tmp_path, agent):
    """Temporary project directory with agent config dir stub."""
    config_dir = {
        "claude-code": ".claude",
        "openclaw": ".openclaw",
    }[agent]
    (tmp_path / config_dir).mkdir(exist_ok=True)
    return tmp_path

@pytest.fixture
def ipman_env(project_dir, agent, scope):
    env_name = f"e2e-{uuid4().hex[:8]}"
    run(f"ipman env create {env_name} --agent {agent} --{scope}")
    yield EnvInfo(name=env_name, agent=agent, scope=scope, project=project_dir)
    run(f"ipman env delete {env_name} --{scope}")
```

### 5.3 User/Machine Scope Isolation

```python
@pytest.fixture(autouse=True)
def isolate_user_scope(tmp_path, monkeypatch):
    """Redirect ~/.ipman to tmp_path to avoid polluting real HOME."""
    fake_home = tmp_path / "fake_home"
    fake_home.mkdir()
    monkeypatch.setenv("IPMAN_HOME", str(fake_home / ".ipman"))
```

### 5.4 GitHub Identity Fixtures (Publish Tests)

```python
class GitHubIdentity:
    ANONYMOUS = "anonymous"
    OWNER     = "owner"
    USER_A    = "user_a"
    USER_B    = "user_b"

@pytest.fixture
def github_owner():
    token = os.environ.get("GH_TOKEN_OWNER")
    if not token:
        pytest.skip("GH_TOKEN_OWNER not set")
    return GitHubAuth(identity=GitHubIdentity.OWNER, token=token)

@pytest.fixture
def github_user_a():
    token = os.environ.get("GH_TOKEN_USER_A")
    if not token:
        pytest.skip("GH_TOKEN_USER_A not set")
    return GitHubAuth(identity=GitHubIdentity.USER_A, token=token)

@pytest.fixture
def github_user_b():
    token = os.environ.get("GH_TOKEN_USER_B")
    if not token:
        pytest.skip("GH_TOKEN_USER_B not set")
    return GitHubAuth(identity=GitHubIdentity.USER_B, token=token)
```

## 6. Test Scenarios

### 6.1 test_env_lifecycle.py

Parametrized by: `agent x scope`

| Test | Description |
|------|-------------|
| `test_create_env` | Create environment, verify directory structure and metadata.yaml |
| `test_create_duplicate_env_fails` | Duplicate name raises error |
| `test_activate_env` | Activate creates correct symlink |
| `test_activate_generates_correct_shell_script` | Verify bash/zsh/fish/powershell scripts (skip irrelevant shells per OS) |
| `test_switch_env` | Switch from env-a to env-b, symlink updated |
| `test_deactivate_env` | Deactivate removes symlink, physical storage preserved |
| `test_delete_env` | Delete removes physical storage |
| `test_list_envs` | List returns all created environments |
| `test_status_shows_active` | Status shows currently active environment |
| `test_env_isolation_across_scopes` | Same name in different scopes do not collide |

### 6.2 test_symlink_integrity.py

| Test | Description |
|------|-------------|
| `test_symlink_created_correctly` | Agent config dir is symlink (Unix) or junction (Windows) |
| `test_symlink_target_points_to_env_storage` | Target path is correct |
| `test_symlink_survives_file_write` | Writing files inside symlink does not break it |
| `test_symlink_survives_nested_dir_creation` | Creating subdirs inside does not replace symlink with real dir |
| `test_junction_on_windows` | Windows uses junction (no Developer Mode needed) |
| `test_symlink_after_rapid_toggle` | Rapid activate/deactivate/activate — state consistent |
| `test_real_dir_replaced_by_symlink` | Existing physical dir correctly converted (backup + symlink) |
| `test_broken_symlink_recovery` | Detect and recover from broken symlink target |

### 6.3 test_init_order.py

Parametrized by: `agent x scope x init_order(ipman_first, agent_first)`

| Test | Description |
|------|-------------|
| `test_env_functional_regardless_of_init_order` | Both orders produce a working environment |
| `test_existing_files_preserved_when_agent_first` | Agent-generated config files survive ipman takeover (--inherit) |
| `test_skill_visible_after_late_ipman_init` | Pre-installed skills remain visible after ipman activate --inherit |
| `test_symlink_replaces_real_dir_correctly` | Physical dir becomes symlink, content migrated, backup exists |
| `test_ipman_first_then_agent_does_not_break_symlink` | Agent first launch does not overwrite the symlink |
| `test_both_orders_produce_equivalent_state` | Side-by-side comparison: identical env status and skill lists |

### 6.4 test_pack_roundtrip.py

| Test | Description |
|------|-------------|
| `test_pack_empty_env` | Empty env produces valid .ip.yaml |
| `test_pack_with_skills` | Pack includes installed skills |
| `test_pack_install_roundtrip` | Pack env-a -> install into env-b -> skill lists match |
| `test_pack_preserves_metadata` | name/version/description/author round-trip correctly |

### 6.5 test_publish_workflow.py

#### Happy Path

| Test | Description |
|------|-------------|
| `test_publish_skill_happy_path` | Authenticated user publishes skill, PR created |
| `test_publish_skill_duplicate_friendly` | Re-publish same skill gives friendly message |
| `test_publish_generates_correct_registry` | Registry YAML format and content correct |
| `test_publish_ip_happy_path` | Publish IP package successfully |
| `test_publish_ip_with_dependencies` | Dependencies in registry are complete |

#### Cross-Account Security Matrix

| Test | Description |
|------|-------------|
| `test_anonymous_publish_rejected` | No token -> explicit rejection |
| `test_expired_token_publish_rejected` | Invalid token -> error, not silent failure |
| `test_publish_uses_correct_author` | Registry author matches GitHub username |
| `test_user_cannot_overwrite_others_skill` | user_b cannot overwrite @user_a/skill-x |
| `test_user_can_update_own_skill` | Same user can publish version update |
| `test_pr_author_matches_registry_author` | PR author == registry file author |
| `test_pr_only_modifies_own_namespace` | PR only touches registry/@own_username/ |
| `test_fork_cleanup_after_publish` | Fork branch cleaned up post-publish |
| `test_concurrent_publish_no_conflict` | Simultaneous publishes from different users succeed |
| `test_publish_high_risk_skill_blocked` | HIGH/EXTREME risk blocked at publish time |
| `test_publish_path_traversal_blocked` | Skill name with ../ rejected |

### 6.6 test_skill_install.py

| Test | Description |
|------|-------------|
| `test_install_skill_from_local` | Install local skill file, visible in agent |
| `test_uninstall_skill` | Uninstall removes from agent |
| `test_install_skill_from_hub` | Install from iphub registry |
| `test_install_with_security_vetting` | Suspicious skill handled per security mode |
| `test_skill_persists_across_deactivate_reactivate` | Skill survives deactivate/reactivate cycle |

### 6.7 test_ip_install.py

| Test | Description |
|------|-------------|
| `test_install_ip_from_local_file` | All skills in .ip.yaml installed |
| `test_install_ip_with_deps` | Dependencies recursively resolved and installed |
| `test_install_ip_from_hub` | Install IP via iphub reference |

### 6.8 test_agent_session.py

| Test | Description |
|------|-------------|
| `test_symlink_survives_agent_session` | Core: activate -> agent session -> .claude still symlink |
| `test_installed_skill_visible_in_session` | Skill usable during agent session |
| `test_env_switch_reflected_in_new_session` | After switch, new session sees new env's skills |
| `test_agent_session_does_not_corrupt_metadata` | metadata.yaml unchanged after session |
| `test_concurrent_sessions_different_projects` | Two projects, two envs, simultaneous sessions, no interference |

## 7. Helpers

### 7.1 AgentManager

```python
class AgentManager:
    SESSION_COMMANDS = {
        "claude-code": {"cmd": ["claude", "--print"], "prompt_arg": "positional"},
        "openclaw":    {"cmd": ["openclaw", "run"],   "prompt_arg": "positional"},
    }

    CLI_COMMANDS = {
        "claude-code": {
            "install":   ["claude", "plugin", "install"],
            "uninstall": ["claude", "plugin", "uninstall"],
            "list":      ["claude", "plugin", "list", "--json"],
        },
        "openclaw": {
            "install":   ["clawhub", "install"],
            "uninstall": ["clawhub", "uninstall"],
            "list":      ["clawhub", "list", "--json"],
        },
    }

    def is_installed(name) -> bool: ...
    def run_cli(*args, timeout=30) -> CompletedProcess: ...
    def install_skill(skill_path) -> bool: ...
    def start_session(prompt, timeout=60) -> SessionResult: ...
    def list_skills() -> list[dict]: ...
```

### 7.2 PlatformAssert

```python
class PlatformAssert:
    @staticmethod
    def is_symlink(path: Path) -> bool: ...
    @staticmethod
    def symlink_target(path: Path) -> Path: ...
    @staticmethod
    def assert_symlink_alive(path: Path, expected_target: Path): ...
    @staticmethod
    def assert_not_real_dir(path: Path): ...
```

### 7.3 GitHub Cleanup

```python
def cleanup_pr(repo: str, pr_number: int, token: str): ...
def cleanup_fork_branch(repo: str, branch: str, token: str): ...
def cleanup_registry_file(repo: str, path: str, token: str): ...
```

## 8. CI/CD Integration

### 8.1 Dual Workflow Architecture

**e2e-fast.yml** — Runs on every push/PR:
- Layers 1 + 2 (platform + agent CLI)
- No secrets required
- Matrix: OS(3) x Agent(2) = 6 jobs
- Duration: ~5 min

**e2e-full.yml** — Runs daily (04:00 UTC) + release tags + manual:
- All layers 1-3 + publish security + init order
- Requires secrets: ANTHROPIC_API_KEY, GH_TOKEN_OWNER, GH_TOKEN_USER_A, GH_TOKEN_USER_B
- Matrix: OS(3) x Agent(2) = 6 jobs + 1 dedicated publish security job
- Duration: ~15 min

### 8.2 Secrets & Variables

| Type     | Name                | Description                                    |
|----------|---------------------|------------------------------------------------|
| Secret   | `ANTHROPIC_API_KEY` | Claude Code API key for Layer 3 sessions       |
| Secret   | `GH_TOKEN_OWNER`    | iphub-test repo owner PAT (repo + workflow)    |
| Secret   | `GH_TOKEN_USER_A`   | Test user A PAT (repo + read:user)             |
| Secret   | `GH_TOKEN_USER_B`   | Test user B PAT (repo + read:user)             |
| Variable | `IPHUB_TEST_REPO`   | Test repo full name, e.g. `twisker/iphub-test` |

### 8.3 iphub-test Repository

Pre-created test repository mirroring iphub structure:

```
twisker/iphub-test/
  index.yaml
  registry/
    @test-owner/
  .github/workflows/
    auto-merge.yml
  README.md
```

### 8.4 Publish Security Tests — Separate Job

Publish security tests run as a dedicated job on ubuntu-latest only. Rationale: publish logic is platform-independent (uses `gh` CLI), running on all 3 OS would generate 6x GitHub API load and cleanup burden with no additional coverage.

### 8.5 Local Execution

```bash
# Platform tests only (no secrets needed)
uv run pytest tests/e2e/ -m "platform" -v

# Platform + agent CLI (needs local agent installation)
uv run pytest tests/e2e/ -m "platform or agent_cli" --agent claude-code -v

# Full suite (needs env vars)
export ANTHROPIC_API_KEY=sk-...
export GH_TOKEN_OWNER=ghp_...
uv run pytest tests/e2e/ -v
```

## 9. Extensibility

Adding a new agent (e.g., Cursor, Windsurf) requires only 3 steps:

1. **Add to `AGENT_SCOPES`** in conftest.py with its scope mapping.
2. **Add to `SESSION_COMMANDS` and `CLI_COMMANDS`** in agent_manager.py.
3. **Add fixture data** in `tests/e2e/fixtures/skills/<agent>/hello-world/`.

No test code modifications needed — parametrization automatically includes the new agent in the full matrix.

## 10. Dependencies

```toml
# pyproject.toml [project.optional-dependencies]
e2e = [
    "pytest-timeout>=2.2",       # Prevent agent session hangs
    "pytest-xdist>=3.5",         # Parallel execution (optional)
    "pytest-rerunfailures>=14",  # Retry on network flakiness (publish tests)
]
```

## 11. Custom pytest CLI Options

```python
def pytest_addoption(parser):
    parser.addoption("--agent", default=None,
        help="Only run tests for this agent (claude-code, openclaw)")
    parser.addoption("--iphub-repo", default=None,
        help="Override iphub test repo (default: env IPHUB_TEST_REPO)")
```
