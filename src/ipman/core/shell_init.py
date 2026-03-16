"""Shell detection and config file path resolution for ipman shell init."""

from __future__ import annotations

import os
import platform
from pathlib import Path

MARKER_START = "# >>> ipman init >>>"
MARKER_END = "# <<< ipman init <<<"
SUPPORTED_SHELLS = ("bash", "zsh", "fish", "powershell")


def detect_shell() -> str:
    """Detect the current shell from environment variables.

    Checks $SHELL for zsh, bash, fish (zsh before bash to avoid the
    known bug where both match 'bash'). Falls back to checking
    $PSModulePath for PowerShell, then defaults to 'bash'.
    """
    shell_path = os.environ.get("SHELL", "")
    if "zsh" in shell_path:
        return "zsh"
    if "bash" in shell_path:
        return "bash"
    if "fish" in shell_path:
        return "fish"
    if os.environ.get("PSModulePath"):  # noqa: SIM112
        return "powershell"
    return "bash"


def config_file_path(shell: str) -> Path:
    """Return the config file path for the given shell.

    Args:
        shell: One of 'bash', 'zsh', 'fish', 'powershell'.

    Returns:
        Path to the shell's config file.

    Raises:
        ValueError: If the shell is not supported.
    """
    home = Path.home()
    if shell == "bash":
        return home / ".bashrc"
    if shell == "zsh":
        return home / ".zshrc"
    if shell == "fish":
        return home / ".config" / "fish" / "config.fish"
    if shell == "powershell":
        profile = "Microsoft.PowerShell_profile.ps1"
        if platform.system() == "Windows":
            return home / "Documents" / "PowerShell" / profile
        return home / ".config" / "PowerShell" / profile
    msg = f"Unsupported shell: {shell}"
    raise ValueError(msg)
