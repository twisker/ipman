"""Cross-platform filesystem assertions for E2E tests."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def is_windows() -> bool:
    return sys.platform == "win32"


def has_machine_scope_permission() -> bool:
    """Check if current process can write to machine scope paths."""
    if is_windows():
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0  # type: ignore[union-attr]
        except (AttributeError, OSError):
            return False
    return os.geteuid() == 0 if hasattr(os, "geteuid") else False


class PlatformAssert:
    """Cross-platform symlink/junction assertions."""

    @staticmethod
    def is_symlink(path: Path) -> bool:
        """Check if path is symlink (Unix) or junction (Windows)."""
        if path.is_symlink():
            return True
        if is_windows() and path.is_dir():
            try:
                os.readlink(path)
                return True
            except OSError:
                return False
        return False

    @staticmethod
    def symlink_target(path: Path) -> Path:
        """Return the target of a symlink/junction."""
        return Path(os.readlink(path))

    @staticmethod
    def assert_symlink_alive(path: Path, expected_target: Path) -> None:
        """Assert symlink exists and points to expected target."""
        assert PlatformAssert.is_symlink(path), (
            f"Expected symlink at {path}, but it is "
            f"{'a regular dir' if path.is_dir() else 'missing'}"
        )
        actual = PlatformAssert.symlink_target(path).resolve()
        expected = expected_target.resolve()
        assert actual == expected, (
            f"Symlink target mismatch: {actual} != {expected}"
        )

    @staticmethod
    def assert_not_real_dir(path: Path) -> None:
        """Assert path is NOT a real (non-symlink) directory."""
        if path.exists() and path.is_dir() and not PlatformAssert.is_symlink(path):
            raise AssertionError(
                f"Expected symlink or non-existent, but {path} is a real directory"
            )
