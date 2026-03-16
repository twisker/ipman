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


def _bash_injection() -> str:
    """Return the bash/zsh shell function wrapper."""
    return f"""{MARKER_START}
# !! Contents within this block are managed by 'ipman init' !!
ipman() {{
    if [ "$1" = "env" ] && [ "$2" = "activate" ]; then
        shift 2
        eval "$(command ipman env activate "$@")"
    elif [ "$1" = "env" ] && [ "$2" = "deactivate" ]; then
        shift 2
        eval "$(command ipman env deactivate "$@")"
    else
        command ipman "$@"
    fi
}}
{MARKER_END}"""


def _fish_injection() -> str:
    """Return the fish shell function wrapper."""
    return f"""{MARKER_START}
# !! Contents within this block are managed by 'ipman init' !!
function ipman
    if test "$argv[1]" = "env"; and test "$argv[2]" = "activate"
        eval (command ipman env activate $argv[3..])
    else if test "$argv[1]" = "env"; and test "$argv[2]" = "deactivate"
        eval (command ipman env deactivate $argv[3..])
    else
        command ipman $argv
    end
end
{MARKER_END}"""


def _powershell_injection() -> str:
    """Return the PowerShell function wrapper."""
    return f"""{MARKER_START}
# !! Contents within this block are managed by 'ipman init' !!
function ipman {{
    $ipmanExe = (Get-Command ipman -CommandType Application).Source
    if ($args[0] -eq 'env' -and $args[1] -eq 'activate') {{
        $remaining = @($args | Select-Object -Skip 2)
        $script = (& $ipmanExe env activate @remaining) -join "`n"
        Invoke-Expression $script
    }} elseif ($args[0] -eq 'env' -and $args[1] -eq 'deactivate') {{
        $remaining = @($args | Select-Object -Skip 2)
        $script = (& $ipmanExe env deactivate @remaining) -join "`n"
        Invoke-Expression $script
    }} else {{
        & $ipmanExe @args
    }}
}}
{MARKER_END}"""


def generate_injection(shell: str) -> str:
    """Generate the shell function wrapper with markers for the given shell.

    Args:
        shell: One of 'bash', 'zsh', 'fish', 'powershell'.

    Returns:
        The injection content string with MARKER_START and MARKER_END.

    Raises:
        ValueError: If the shell is not supported.
    """
    if shell in ("bash", "zsh"):
        return _bash_injection()
    if shell == "fish":
        return _fish_injection()
    if shell == "powershell":
        return _powershell_injection()
    msg = f"Unsupported shell: {shell}"
    raise ValueError(msg)
