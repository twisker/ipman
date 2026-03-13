"""Cross-platform symlink utilities."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def create_symlink(target: Path, link: Path) -> None:
    """Create a symlink at `link` pointing to `target`.

    On Windows, uses directory junctions as a fallback if symlinks
    require elevated privileges.
    """
    target = target.resolve()
    _validate_no_traversal(target)

    if link.exists() or link.is_symlink():
        msg = f"Link path already exists: {link}"
        raise FileExistsError(msg)

    if sys.platform == "win32":
        _create_windows_link(target, link)
    else:
        link.symlink_to(target)


def remove_symlink(link: Path) -> None:
    """Remove a symlink (or junction on Windows).

    Raises ValueError if the path is not a symlink.
    """
    if not link.is_symlink():
        if sys.platform == "win32" and link.is_dir():
            # Could be a junction on Windows
            os.rmdir(link)
            return
        msg = f"Not a symlink: {link}"
        raise ValueError(msg)
    link.unlink()


def is_symlink(path: Path) -> bool:
    """Check if path is a symlink (or junction on Windows)."""
    if path.is_symlink():
        return True
    if sys.platform == "win32" and path.is_dir():
        # Check for junction point
        try:
            return bool(os.readlink(path))
        except OSError:
            return False
    return False


def resolve_symlink(path: Path) -> Path | None:
    """Return the target of a symlink, or None if not a symlink."""
    if is_symlink(path):
        return Path(os.readlink(path))
    return None


def _validate_no_traversal(target: Path) -> None:
    """Validate that the resolved target doesn't traverse outside expectations."""
    resolved = target.resolve()
    if ".." in resolved.parts:
        msg = f"Path traversal detected: {target}"
        raise ValueError(msg)


def _create_windows_link(target: Path, link: Path) -> None:
    """Create a symlink or directory junction on Windows."""
    try:
        link.symlink_to(target)
    except OSError:
        # Fallback to directory junction (no admin needed)
        import subprocess

        subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],
            check=True,
            capture_output=True,
        )
