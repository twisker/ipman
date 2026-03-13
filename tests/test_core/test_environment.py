"""Tests for virtual environment management."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from ipman.agents.claude_code import ClaudeCodeAdapter
from ipman.core.environment import (
    Scope,
    activate_env,
    create_env,
    deactivate_env,
    delete_env,
    generate_activate_script,
    generate_deactivate_script,
    list_envs,
)


@pytest.fixture
def adapter():
    return ClaudeCodeAdapter()


@pytest.fixture
def project(tmp_path):
    """A temporary project directory."""
    return tmp_path / "myproject"


@pytest.fixture
def project_with_claude(project):
    """A project that already has a .claude directory."""
    project.mkdir()
    claude_dir = project / ".claude"
    claude_dir.mkdir()
    (claude_dir / "settings.local.json").write_text("{}")
    (claude_dir / "skills").mkdir()
    (claude_dir / "skills" / "my-skill").mkdir()
    return project


class TestCreateEnv:
    def test_create_basic(self, project, adapter):
        project.mkdir()
        env_path = create_env("test", adapter, Scope.PROJECT, project)

        assert env_path.exists()
        assert (env_path / "skills").is_dir()
        assert (env_path / "env.yaml").exists()

        meta = yaml.safe_load((env_path / "env.yaml").read_text())
        assert meta["name"] == "test"
        assert meta["scope"] == "project"
        assert meta["agent"] == "claude-code"

    def test_create_writes_project_config(self, project, adapter):
        project.mkdir()
        create_env("test", adapter, Scope.PROJECT, project)

        config_file = project / ".ipman" / "ipman.yaml"
        assert config_file.exists()
        config = yaml.safe_load(config_file.read_text())
        assert config["agent"] == "claude-code"
        assert config["agent_config_dir"] == ".claude"
        assert config["active_env"] is None

    def test_create_duplicate_fails(self, project, adapter):
        project.mkdir()
        create_env("test", adapter, Scope.PROJECT, project)
        with pytest.raises(FileExistsError):
            create_env("test", adapter, Scope.PROJECT, project)

    def test_create_multiple_envs(self, project, adapter):
        project.mkdir()
        create_env("env1", adapter, Scope.PROJECT, project)
        create_env("env2", adapter, Scope.PROJECT, project)

        envs_dir = project / ".ipman" / "envs"
        assert (envs_dir / "env1").exists()
        assert (envs_dir / "env2").exists()

    def test_create_with_inherit(self, project_with_claude, adapter):
        env_path = create_env(
            "test", adapter, Scope.PROJECT,
            project_with_claude, inherit=True,
        )
        # Should have copied the skills directory
        assert (env_path / "skills" / "my-skill").is_dir()
        # Should have copied settings
        assert (env_path / "settings.local.json").exists()

    def test_create_user_scope(self, tmp_path, adapter, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        env_path = create_env("global-env", adapter, Scope.USER)
        assert env_path == tmp_path / ".ipman" / "envs" / "global-env"
        assert env_path.exists()


class TestActivateDeactivate:
    def test_activate_no_existing_config(self, project, adapter):
        """Activate when no .claude/ exists yet."""
        project.mkdir()
        create_env("test", adapter, Scope.PROJECT, project)
        env_path = activate_env("test", Scope.PROJECT, project)

        agent_config = project / ".claude"
        assert agent_config.is_symlink()
        assert agent_config.resolve() == env_path.resolve()

    def test_activate_backs_up_existing(self, project_with_claude, adapter):
        """Activate should backup existing .claude/ to .claude.bak/."""
        create_env("test", adapter, Scope.PROJECT, project_with_claude)
        activate_env("test", Scope.PROJECT, project_with_claude)

        assert (project_with_claude / ".claude").is_symlink()
        assert (project_with_claude / ".claude.bak").is_dir()
        assert (project_with_claude / ".claude.bak" / "settings.local.json").exists()

    def test_deactivate_restores_backup(self, project_with_claude, adapter):
        """Deactivate should restore .claude.bak/ to .claude/."""
        create_env("test", adapter, Scope.PROJECT, project_with_claude)
        activate_env("test", Scope.PROJECT, project_with_claude)
        deactivate_env(project_with_claude)

        agent_config = project_with_claude / ".claude"
        assert not agent_config.is_symlink()
        assert agent_config.is_dir()
        assert (agent_config / "settings.local.json").exists()

    def test_switch_envs(self, project, adapter):
        """Switching from one env to another should repoint the symlink."""
        project.mkdir()
        create_env("env1", adapter, Scope.PROJECT, project)
        create_env("env2", adapter, Scope.PROJECT, project)

        env1_path = activate_env("env1", Scope.PROJECT, project)
        assert (project / ".claude").resolve() == env1_path.resolve()

        env2_path = activate_env("env2", Scope.PROJECT, project)
        assert (project / ".claude").resolve() == env2_path.resolve()

    def test_activate_nonexistent_fails(self, project, adapter):
        project.mkdir()
        create_env("test", adapter, Scope.PROJECT, project)
        with pytest.raises(FileNotFoundError):
            activate_env("nope", Scope.PROJECT, project)

    def test_deactivate_when_not_active_fails(self, project, adapter):
        project.mkdir()
        create_env("test", adapter, Scope.PROJECT, project)
        with pytest.raises(RuntimeError):
            deactivate_env(project)

    def test_activate_updates_config(self, project, adapter):
        project.mkdir()
        create_env("test", adapter, Scope.PROJECT, project)
        activate_env("test", Scope.PROJECT, project)

        config = yaml.safe_load(
            (project / ".ipman" / "ipman.yaml").read_text()
        )
        assert config["active_env"] == "test"

    def test_deactivate_clears_config(self, project, adapter):
        project.mkdir()
        create_env("test", adapter, Scope.PROJECT, project)
        activate_env("test", Scope.PROJECT, project)
        deactivate_env(project)

        config = yaml.safe_load(
            (project / ".ipman" / "ipman.yaml").read_text()
        )
        assert config["active_env"] is None


class TestDeleteEnv:
    def test_delete_basic(self, project, adapter):
        project.mkdir()
        env_path = create_env("test", adapter, Scope.PROJECT, project)
        delete_env("test", Scope.PROJECT, project)
        assert not env_path.exists()

    def test_delete_active_deactivates_first(self, project, adapter):
        project.mkdir()
        create_env("test", adapter, Scope.PROJECT, project)
        activate_env("test", Scope.PROJECT, project)
        delete_env("test", Scope.PROJECT, project)

        assert not (project / ".claude").is_symlink()

    def test_delete_nonexistent_fails(self, project, adapter):
        project.mkdir()
        create_env("dummy", adapter, Scope.PROJECT, project)
        with pytest.raises(FileNotFoundError):
            delete_env("nope", Scope.PROJECT, project)


class TestListEnvs:
    def test_list_empty(self, project):
        project.mkdir()
        result = list_envs(Scope.PROJECT, project)
        assert result == []

    def test_list_multiple(self, project, adapter):
        project.mkdir()
        create_env("a", adapter, Scope.PROJECT, project)
        create_env("b", adapter, Scope.PROJECT, project)

        result = list_envs(Scope.PROJECT, project)
        names = [e["name"] for e in result]
        assert "a" in names
        assert "b" in names

    def test_list_shows_active(self, project, adapter):
        project.mkdir()
        create_env("a", adapter, Scope.PROJECT, project)
        create_env("b", adapter, Scope.PROJECT, project)
        activate_env("a", Scope.PROJECT, project)

        result = list_envs(Scope.PROJECT, project)
        active = [e for e in result if e["active"]]
        assert len(active) == 1
        assert active[0]["name"] == "a"


class TestShellScripts:
    def test_bash_activate(self):
        script = generate_activate_script("myenv", "bash")
        assert 'IPMAN_ENV="myenv"' in script
        assert "[ipman:myenv]" in script

    def test_bash_deactivate(self):
        script = generate_deactivate_script("bash")
        assert "unset IPMAN_ENV" in script

    def test_fish_activate(self):
        script = generate_activate_script("myenv", "fish")
        assert "IPMAN_ENV" in script
        assert "[ipman:myenv]" in script

    def test_powershell_activate(self):
        script = generate_activate_script("myenv", "powershell")
        assert "IPMAN_ENV" in script
