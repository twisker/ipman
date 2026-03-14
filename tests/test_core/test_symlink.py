"""Tests for cross-platform symlink utilities."""

from __future__ import annotations

from pathlib import Path

import pytest

from ipman.utils.symlink import (
    create_symlink,
    is_symlink,
    remove_symlink,
    resolve_symlink,
)


@pytest.fixture
def target_dir(tmp_path):
    d = tmp_path / "target"
    d.mkdir()
    (d / "file.txt").write_text("hello")
    return d


class TestCreateSymlink:
    def test_create_basic(self, tmp_path, target_dir):
        link = tmp_path / "mylink"
        create_symlink(target_dir, link)

        assert link.is_symlink()
        assert (link / "file.txt").read_text() == "hello"

    def test_create_fails_if_exists(self, tmp_path, target_dir):
        link = tmp_path / "mylink"
        link.mkdir()
        with pytest.raises(FileExistsError):
            create_symlink(target_dir, link)

    def test_create_fails_if_symlink_exists(self, tmp_path, target_dir):
        link = tmp_path / "mylink"
        link.symlink_to(target_dir)
        with pytest.raises(FileExistsError):
            create_symlink(target_dir, link)


class TestRemoveSymlink:
    def test_remove_basic(self, tmp_path, target_dir):
        link = tmp_path / "mylink"
        link.symlink_to(target_dir)
        remove_symlink(link)
        assert not link.exists()
        # Target should still exist
        assert target_dir.exists()

    def test_remove_non_symlink_fails(self, tmp_path):
        real_dir = tmp_path / "realdir"
        real_dir.mkdir()
        (real_dir / "keep.txt").write_text("keep")  # non-empty dir
        with pytest.raises((ValueError, OSError)):
            remove_symlink(real_dir)


class TestIsSymlink:
    def test_real_dir_is_not_symlink(self, tmp_path):
        d = tmp_path / "real"
        d.mkdir()
        assert not is_symlink(d)

    def test_symlink_is_detected(self, tmp_path, target_dir):
        link = tmp_path / "mylink"
        link.symlink_to(target_dir)
        assert is_symlink(link)

    def test_nonexistent_is_not_symlink(self, tmp_path):
        assert not is_symlink(tmp_path / "nope")


class TestResolveSymlink:
    def test_resolve_returns_target(self, tmp_path, target_dir):
        link = tmp_path / "mylink"
        link.symlink_to(target_dir)
        resolved = resolve_symlink(link)
        assert resolved is not None
        # Normalize to handle Windows \\?\ extended-length path prefix
        def _normalize(p: Path) -> str:
            s = str(p.resolve())
            return s.removeprefix("\\\\?\\")
        assert _normalize(Path(resolved)) == _normalize(target_dir)

    def test_resolve_non_symlink_returns_none(self, tmp_path):
        d = tmp_path / "real"
        d.mkdir()
        assert resolve_symlink(d) is None
