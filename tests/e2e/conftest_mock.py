"""Fixtures for mock clawhub e2e tests."""
from __future__ import annotations

import os
import shutil
import stat
import sys
from pathlib import Path

import pytest

MOCK_CLAWHUB_DIR = Path(__file__).parent / "mock_clawhub"
MOCK_PY = MOCK_CLAWHUB_DIR / "clawhub_mock.py"


@pytest.fixture
def mock_clawhub_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Set up mock clawhub on PATH and return the state directory.

    Creates a platform-appropriate wrapper that delegates to the
    Python mock script (clawhub_mock.py) for cross-platform portability.
    """
    state_dir = tmp_path / "clawhub_state"
    state_dir.mkdir()
    monkeypatch.setenv("MOCK_CLAWHUB_STATE", str(state_dir))

    mock_dir = tmp_path / "mock_bin"
    mock_dir.mkdir()

    # Copy the Python mock script
    py_dest = mock_dir / "clawhub_mock.py"
    shutil.copy2(MOCK_PY, py_dest)

    # Find the Python interpreter
    python_exe = sys.executable

    if sys.platform == "win32":
        # Create a .exe-like wrapper via a .cmd file
        wrapper = mock_dir / "clawhub.cmd"
        wrapper.write_text(
            f'@echo off\n"{python_exe}" "{py_dest}" %*\n',
            encoding="utf-8",
        )
        # Ensure PATHEXT includes .CMD
        pathext = os.environ.get("PATHEXT", ".COM;.EXE;.BAT;.CMD")
        if ".CMD" not in pathext.upper():
            pathext = f".CMD;{pathext}"
        monkeypatch.setenv("PATHEXT", pathext)
    else:
        # Create a bash wrapper
        wrapper = mock_dir / "clawhub"
        wrapper.write_text(
            f'#!/usr/bin/env bash\nexec "{python_exe}" "{py_dest}" "$@"\n',
            encoding="utf-8",
        )
        wrapper.chmod(wrapper.stat().st_mode | stat.S_IEXEC)

    # Also create mock openclaw script
    oc_mock_py = MOCK_CLAWHUB_DIR / "openclaw_mock.py"
    oc_py_dest = mock_dir / "openclaw_mock.py"
    shutil.copy2(oc_mock_py, oc_py_dest)

    if sys.platform == "win32":
        oc_wrapper = mock_dir / "openclaw.cmd"
        oc_wrapper.write_text(
            f'@echo off\n"{python_exe}" "{oc_py_dest}" %*\n',
            encoding="utf-8",
        )
    else:
        oc_wrapper = mock_dir / "openclaw"
        oc_wrapper.write_text(
            f'#!/usr/bin/env bash\nexec "{python_exe}" "{oc_py_dest}" "$@"\n',
            encoding="utf-8",
        )
        oc_wrapper.chmod(oc_wrapper.stat().st_mode | stat.S_IEXEC)

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
    fake_home.mkdir(exist_ok=True)
    monkeypatch.setenv("IPMAN_HOME", str(fake_home / ".ipman"))
    fake_machine = tmp_path / "fake_machine"
    fake_machine.mkdir(exist_ok=True)
    monkeypatch.setenv("IPMAN_MACHINE_ROOT", str(fake_machine / "ipman"))

    return project
