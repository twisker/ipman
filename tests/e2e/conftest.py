"""Core fixtures for E2E tests."""

from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

import pytest

from .helpers.agent_manager import AgentManager
from .helpers.platform_utils import has_machine_scope_permission
from .helpers.run import EnvInfo, GitHubAuth, PublishContext, run_ipman

# ---------------------------------------------------------------------------
# Agent x Scope mapping
# ---------------------------------------------------------------------------

AGENT_SCOPES: dict[str, dict[str, str | None]] = {
    "claude-code": {
        "project": "project",
        "user": "user",
        "machine": "machine",
    },
    "openclaw": {
        "project": "workspace",
        "user": "local",
        "machine": None,
    },
}


def _agent_supports_scope(agent: str, scope: str) -> bool:
    return AGENT_SCOPES.get(agent, {}).get(scope) is not None


# ---------------------------------------------------------------------------
# pytest hooks
# ---------------------------------------------------------------------------

def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--agent", default=None,
                     help="Only run tests for this agent (claude-code, openclaw)")
    parser.addoption("--iphub-repo", default=None,
                     help="Override iphub test repo (default: env IPHUB_TEST_REPO)")


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Apply per-marker timeouts."""
    timeout_map = {
        "platform": 30, "agent_cli": 60, "agent_session": 120,
        "publish": 90, "symlink": 30,
    }
    for item in items:
        for marker_name, timeout in timeout_map.items():
            if marker_name in [m.name for m in item.iter_markers()]:
                item.add_marker(pytest.mark.timeout(timeout))
                break


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(params=["claude-code", "openclaw"])
def agent(request: pytest.FixtureRequest) -> str:
    name: str = request.param
    agent_filter = request.config.getoption("--agent", default=None)
    if agent_filter and agent_filter != name:
        pytest.skip(f"Filtered to --agent {agent_filter}")
    if not AgentManager.is_installed(name):
        pytest.skip(f"{name} not installed on this system")
    return name


@pytest.fixture(params=["project", "user", "machine"])
def scope(request: pytest.FixtureRequest, agent: str) -> str:
    s: str = request.param
    if not _agent_supports_scope(agent, s):
        pytest.skip(f"{agent} does not support scope '{s}'")
    if s == "machine" and not has_machine_scope_permission():
        pytest.skip("machine scope requires elevated permissions")
    return s


@pytest.fixture(autouse=True)
def isolate_scopes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Redirect ipman storage to tmp_path for test isolation."""
    fake_home = tmp_path / "fake_home"
    fake_home.mkdir()
    monkeypatch.setenv("IPMAN_HOME", str(fake_home / ".ipman"))
    fake_machine = tmp_path / "fake_machine"
    fake_machine.mkdir()
    monkeypatch.setenv("IPMAN_MACHINE_ROOT", str(fake_machine / "ipman"))


@pytest.fixture
def project_dir(tmp_path: Path, agent: str) -> Path:
    project = tmp_path / "project"
    project.mkdir()
    config_dir_name = AgentManager.AGENT_CONFIG_DIR[agent]
    (project / config_dir_name).mkdir()
    return project


@pytest.fixture
def agent_manager(agent: str, project_dir: Path) -> AgentManager:
    return AgentManager(agent, project_dir)


@pytest.fixture
def ipman_env(project_dir: Path, agent: str, scope: str) -> EnvInfo:
    env_name = f"e2e-{uuid4().hex[:8]}"
    run_ipman("env", "create", env_name, "--agent", agent, f"--{scope}",
              cwd=project_dir)
    info = EnvInfo(name=env_name, agent=agent, scope=scope, project=project_dir)
    yield info  # type: ignore[misc]
    run_ipman("env", "delete", env_name, f"--{scope}",
              cwd=project_dir, check=False)


@pytest.fixture
def unique_skill_name() -> str:
    return f"e2e-skill-{uuid4().hex[:8]}"


@pytest.fixture
def iphub_test_repo(request: pytest.FixtureRequest) -> str:
    cli = request.config.getoption("--iphub-repo", default=None)
    if cli:
        return cli
    repo = os.environ.get("IPHUB_TEST_REPO", "")
    if not repo:
        pytest.skip("IPHUB_TEST_REPO not set")
    return repo


@pytest.fixture
def github_owner() -> GitHubAuth:
    token = os.environ.get("GH_TOKEN_OWNER", "")
    if not token:
        pytest.skip("GH_TOKEN_OWNER not set")
    return GitHubAuth(identity="owner", token=token)


@pytest.fixture
def github_user_a() -> GitHubAuth:
    token = os.environ.get("GH_TOKEN_USER_A", "")
    if not token:
        pytest.skip("GH_TOKEN_USER_A not set")
    return GitHubAuth(identity="user_a", token=token)


@pytest.fixture
def github_user_b() -> GitHubAuth:
    token = os.environ.get("GH_TOKEN_USER_B", "")
    if not token:
        pytest.skip("GH_TOKEN_USER_B not set")
    return GitHubAuth(identity="user_b", token=token)


@pytest.fixture
def publish_context(
    request: pytest.FixtureRequest,
    unique_skill_name: str,
    iphub_test_repo: str,
    github_owner: GitHubAuth,
) -> PublishContext:
    ctx = PublishContext(
        skill_name=unique_skill_name,
        repo=iphub_test_repo,
        token=github_owner.token,
    )

    def _cleanup() -> None:
        from .helpers.github_cleanup import (
            cleanup_fork_branch,
            cleanup_pr,
            cleanup_registry_file,
        )
        for pr_number in ctx.created_prs:
            cleanup_pr(ctx.repo, pr_number, ctx.token)
        for branch in ctx.created_branches:
            cleanup_fork_branch(ctx.repo, branch, ctx.token)
        for path in ctx.created_registry_files:
            cleanup_registry_file(ctx.repo, path, ctx.token)

    request.addfinalizer(_cleanup)
    return ctx
