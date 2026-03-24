"""Fixtures for mock clawhub e2e tests."""
from __future__ import annotations

import os
import shutil
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

    mock_dir = tmp_path / "mock_bin"
    mock_dir.mkdir()

    if sys.platform == "win32":
        # On Windows, use the .bat script
        shutil.copy2(MOCK_CLAWHUB_DIR / "clawhub.bat", mock_dir / "clawhub.bat")
        shutil.copy2(MOCK_CLAWHUB_DIR / "clawhub.bat", mock_dir / "clawhub.cmd")
        # Ensure PATHEXT includes .BAT
        pathext = os.environ.get("PATHEXT", ".COM;.EXE;.BAT;.CMD")
        if ".BAT" not in pathext.upper():
            pathext = f".BAT;{pathext}"
        monkeypatch.setenv("PATHEXT", pathext)
    else:
        # On Unix, use the bash script
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
