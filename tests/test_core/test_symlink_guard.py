"""Tests for symlink_guard context manager."""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from ipman.core.environment import symlink_guard
from ipman.utils.symlink import (
    create_symlink,
    is_symlink,
    remove_symlink,
    resolve_symlink,
)


def _remove_link_or_dir(path: Path) -> None:
    """Remove a symlink/junction or real directory, cross-platform."""
    if is_symlink(path):
        remove_symlink(path)
    elif path.exists():
        shutil.rmtree(path)


def _setup_active_env(project: Path, env_name: str, agent_config_dir: str = ".openclaw") -> Path:
    """Create a fake active ipman environment with symlink."""
    env_path = project / ".ipman" / "envs" / env_name
    env_path.mkdir(parents=True)
    (env_path / "skills").mkdir()
    (env_path / "env.yaml").write_text(
        yaml.dump({"name": env_name, "agent": "openclaw"}),
    )

    ipman_dir = project / ".ipman"
    ipman_dir.mkdir(exist_ok=True)
    (ipman_dir / "ipman.yaml").write_text(
        yaml.dump({
            "agent": "openclaw",
            "agent_config_dir": agent_config_dir,
            "active_env": env_name,
        }),
    )

    link_path = project / agent_config_dir
    if link_path.exists():
        shutil.rmtree(link_path)
    create_symlink(target=env_path, link=link_path)

    return env_path


class TestSymlinkGuardNoOp:
    def test_no_active_env(self, tmp_path: Path) -> None:
        with symlink_guard(tmp_path):
            pass

    def test_no_active_env_in_config(self, tmp_path: Path) -> None:
        ipman_dir = tmp_path / ".ipman"
        ipman_dir.mkdir()
        (ipman_dir / "ipman.yaml").write_text(
            yaml.dump({"agent": "openclaw", "agent_config_dir": ".openclaw", "active_env": None}),
        )
        with symlink_guard(tmp_path):
            pass

    def test_symlink_intact_after_operation(self, tmp_path: Path) -> None:
        env_path = _setup_active_env(tmp_path, "test-env")
        link_path = tmp_path / ".openclaw"

        with symlink_guard(tmp_path):
            (link_path / "new_file.txt").write_text("hello")

        assert is_symlink(link_path)
        assert (env_path / "new_file.txt").exists()


class TestSymlinkGuardRepair:
    def test_symlink_replaced_with_real_dir(self, tmp_path: Path) -> None:
        env_path = _setup_active_env(tmp_path, "test-env")
        link_path = tmp_path / ".openclaw"

        (env_path / "skills" / "old-skill").mkdir(parents=True)

        with symlink_guard(tmp_path):
            _remove_link_or_dir(link_path)
            link_path.mkdir()
            (link_path / "plugins" / "new-ext").mkdir(parents=True)
            (link_path / "plugins" / "new-ext" / "manifest.json").write_text("{}")

        assert is_symlink(link_path)
        assert (env_path / "plugins" / "new-ext" / "manifest.json").exists()
        assert (env_path / "skills" / "old-skill").exists()

    def test_symlink_and_dir_both_gone(self, tmp_path: Path) -> None:
        env_path = _setup_active_env(tmp_path, "test-env")
        link_path = tmp_path / ".openclaw"

        with symlink_guard(tmp_path):
            _remove_link_or_dir(link_path)

        assert is_symlink(link_path)
        resolved_target = resolve_symlink(link_path)
        assert resolved_target is not None
        # Normalize paths to strip Windows junction prefix (\\?\)
        def _norm(p: Path) -> str:
            s = str(p)
            if s.startswith("\\\\?\\"):
                s = s[4:]
            return s
        assert _norm(resolved_target) == _norm(env_path.resolve())

    def test_repair_failure_does_not_raise(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        _setup_active_env(tmp_path, "test-env")
        link_path = tmp_path / ".openclaw"

        def _broken_create(*a, **kw):
            raise PermissionError("simulated")

        with symlink_guard(tmp_path):
            _remove_link_or_dir(link_path)
            monkeypatch.setattr("ipman.core.environment.create_symlink", _broken_create)

        assert not is_symlink(link_path)
