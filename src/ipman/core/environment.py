"""Virtual environment management for IpMan."""

from __future__ import annotations

import enum
import os
import shutil
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from ipman.agents.base import AgentAdapter
from ipman.utils.symlink import (
    create_symlink,
    is_symlink,
    remove_symlink,
    resolve_symlink,
)


class Scope(enum.Enum):
    """Environment scope."""

    PROJECT = "project"
    USER = "user"
    MACHINE = "machine"


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

def get_ipman_home() -> Path:
    """Return the global IpMan home directory (~/.ipman).

    Honors IPMAN_HOME environment variable for testing/custom setups.
    """
    override = os.environ.get("IPMAN_HOME")
    if override:
        return Path(override)
    return Path.home() / ".ipman"


def get_project_ipman_dir(project_path: Path) -> Path:
    """Return the .ipman directory for a project."""
    return project_path / ".ipman"


def get_envs_root(scope: Scope, project_path: Path | None = None) -> Path:
    """Return the envs/ root directory for the given scope."""
    if scope == Scope.PROJECT:
        if project_path is None:
            msg = "project_path is required for project scope"
            raise ValueError(msg)
        return get_project_ipman_dir(project_path) / "envs"
    if scope == Scope.USER:
        return get_ipman_home() / "envs"
    # MACHINE scope
    override = os.environ.get("IPMAN_MACHINE_ROOT")
    if override:
        return Path(override) / "envs"
    # Try config file
    from ipman.core.config import load_config
    cfg = load_config()
    if cfg.machine_env_root:
        return Path(cfg.machine_env_root) / "envs"
    if _is_windows():
        return Path("C:/ProgramData/ipman/envs")
    # Unix: XDG_DATA_HOME fallback before /opt
    xdg_data = os.environ.get("XDG_DATA_HOME", "")
    if xdg_data:
        return Path(xdg_data) / "ipman" / "envs"
    return Path("/opt/ipman/envs")


def get_env_path(name: str, scope: Scope, project_path: Path | None = None) -> Path:
    """Return the full path to a named environment."""
    return get_envs_root(scope, project_path) / name


# ---------------------------------------------------------------------------
# CRUD operations
# ---------------------------------------------------------------------------

def create_env(
    name: str,
    adapter: AgentAdapter,
    scope: Scope = Scope.PROJECT,
    project_path: Path | None = None,
    inherit: bool = False,
) -> Path:
    """Create a new virtual environment.

    Returns the path to the created environment directory.
    """
    if project_path is None:
        project_path = Path.cwd()

    env_path = get_env_path(name, scope, project_path)

    if env_path.exists():
        msg = f"Environment '{name}' already exists at {env_path}"
        raise FileExistsError(msg)

    # Create the environment directory
    env_path.mkdir(parents=True)

    # Initialize agent-specific structure
    adapter.init_env_dir(env_path)

    # Optionally inherit existing skills from current agent config
    if inherit:
        _inherit_existing(adapter, env_path, project_path)

    # Write ipman.yaml project config (for project scope)
    if scope == Scope.PROJECT:
        _ensure_project_config(project_path, adapter)

    # Write env metadata
    _write_env_metadata(env_path, name, scope, adapter)

    return env_path


def delete_env(
    name: str,
    scope: Scope = Scope.PROJECT,
    project_path: Path | None = None,
) -> None:
    """Delete a virtual environment."""
    if project_path is None:
        project_path = Path.cwd()

    env_path = get_env_path(name, scope, project_path)

    if not env_path.exists():
        msg = f"Environment '{name}' does not exist"
        raise FileNotFoundError(msg)

    # Check if this env is currently active — deactivate first
    config = _read_project_config(project_path)
    if config and config.get("active_env") == name:
        deactivate_env(project_path=project_path)

    shutil.rmtree(env_path)


def list_envs(
    scope: Scope = Scope.PROJECT,
    project_path: Path | None = None,
) -> list[dict[str, Any]]:
    """List all environments for the given scope.

    Returns a list of dicts with env metadata.
    """
    if project_path is None:
        project_path = Path.cwd()

    envs_root = get_envs_root(scope, project_path)

    if not envs_root.exists():
        return []

    result = []
    config = _read_project_config(project_path)
    active_name = config.get("active_env") if config else None

    for env_dir in sorted(envs_root.iterdir()):
        if not env_dir.is_dir():
            continue
        meta_file = env_dir / "env.yaml"
        if meta_file.exists():
            meta = yaml.safe_load(meta_file.read_text(encoding="utf-8")) or {}
        else:
            meta = {"name": env_dir.name}
        meta["active"] = meta.get("name", env_dir.name) == active_name
        meta["path"] = str(env_dir)
        result.append(meta)

    return result


# ---------------------------------------------------------------------------
# Activate / Deactivate
# ---------------------------------------------------------------------------

def activate_env(
    name: str,
    scope: Scope = Scope.PROJECT,
    project_path: Path | None = None,
) -> Path:
    """Activate a virtual environment by symlinking the agent config dir.

    Returns the path to the activated environment.
    """
    if project_path is None:
        project_path = Path.cwd()

    env_path = get_env_path(name, scope, project_path)
    if not env_path.exists():
        msg = f"Environment '{name}' does not exist"
        raise FileNotFoundError(msg)

    # Read agent info from env metadata
    meta_file = env_path / "env.yaml"
    if not meta_file.exists():
        msg = f"Environment '{name}' has no metadata (env.yaml missing)"
        raise FileNotFoundError(msg)
    meta = yaml.safe_load(meta_file.read_text(encoding="utf-8")) or {}
    agent_name = meta.get("agent")
    if not agent_name:
        msg = f"Environment '{name}' metadata missing 'agent' field"
        raise ValueError(msg)

    from ipman.agents.registry import get_adapter
    adapter = get_adapter(agent_name)
    agent_config_dir_name = adapter.config_dir_name

    # Ensure project config exists (for all scopes)
    _ensure_project_config(project_path, adapter)

    agent_config_path = project_path / agent_config_dir_name
    backup_path = project_path / f"{agent_config_dir_name}.bak"

    # If already a symlink (another env active), remove it
    if is_symlink(agent_config_path):
        remove_symlink(agent_config_path)
    elif agent_config_path.exists():
        # Real directory — back it up
        if backup_path.exists():
            msg = (
                f"Backup already exists at {backup_path}. "
                "Please resolve manually before activating."
            )
            raise FileExistsError(msg)
        agent_config_path.rename(backup_path)

    # Create the symlink
    create_symlink(target=env_path, link=agent_config_path)

    # Update project config
    _update_project_config(project_path, active_env=name)

    return env_path


def deactivate_env(
    project_path: Path | None = None,
) -> None:
    """Deactivate the current virtual environment."""
    if project_path is None:
        project_path = Path.cwd()

    config = _read_project_config(project_path)
    if not config or not config.get("active_env"):
        msg = "No environment is currently active"
        raise RuntimeError(msg)

    agent_config_dir_name = config.get("agent_config_dir")
    if not agent_config_dir_name:
        # Fall back to reading from the active env's metadata
        active_name = config["active_env"]
        # Try to find the active env across all scopes
        agent_config_dir_name = _resolve_agent_config_dir(active_name, project_path)

    agent_config_path = project_path / agent_config_dir_name
    backup_path = project_path / f"{agent_config_dir_name}.bak"

    # Remove the symlink
    if is_symlink(agent_config_path):
        remove_symlink(agent_config_path)

    # Restore backup if it exists
    if backup_path.exists():
        backup_path.rename(agent_config_path)

    # Clear active env in config
    _update_project_config(project_path, active_env=None)


# ---------------------------------------------------------------------------
# Symlink guard
# ---------------------------------------------------------------------------

@contextmanager
def symlink_guard(project_path: Path | None = None) -> Generator[None, None, None]:
    """Protect symlink integrity across agent CLI operations.

    Wraps agent CLI calls to detect and auto-repair broken symlinks.
    If an agent CLI operation replaces the symlink with a real directory,
    the guard will sync contents back and restore the symlink.
    """
    project_path = project_path or Path.cwd()

    config = _read_project_config(project_path)
    if not config or not config.get("active_env"):
        yield
        return

    agent_config_dir = config.get("agent_config_dir", ".claude")
    link_path = project_path / agent_config_dir
    was_symlink = is_symlink(link_path)
    original_target = resolve_symlink(link_path) if was_symlink else None

    yield

    if not original_target or is_symlink(link_path):
        return

    try:
        if link_path.exists():
            _sync_and_restore_symlink(link_path, original_target)
        else:
            create_symlink(target=original_target, link=link_path)
        import click
        click.secho(
            "\u26a0 Environment link was broken by agent CLI operation. Auto-repaired.",
            fg="yellow", err=True,
        )
    except Exception as exc:
        import click
        click.secho(
            f"\u26a0 Environment link was broken and auto-repair failed: {exc}\n"
            "  Run 'ipman env activate <name>' to manually restore.",
            fg="yellow", err=True,
        )


def _sync_and_restore_symlink(link_path: Path, original_target: Path) -> None:
    """Sync contents from a real dir back to env, then restore the symlink."""
    shutil.copytree(link_path, original_target, dirs_exist_ok=True)
    shutil.rmtree(link_path)
    create_symlink(target=original_target, link=link_path)


# ---------------------------------------------------------------------------
# Shell integration (activate script generation)
# ---------------------------------------------------------------------------

def build_prompt_tag(
    project_path: Path | None = None,
) -> str:
    """Build the compact prompt tag showing active envs across all scopes.

    Format: [ip:<machine><user><project_name>]
      - machine active: *    inactive: omitted
      - user active:    -    inactive: omitted
      - project active: env full name    inactive: omitted

    Examples:
      [ip:*-myenv]  = all three layers active
      [ip:myenv]    = only project
      [ip:*myenv]   = machine + project
      [ip:*-]       = machine + user, no project
    """
    if project_path is None:
        project_path = Path.cwd()

    parts: list[str] = []

    # Machine layer
    machine_envs = list_envs(Scope.MACHINE, project_path)
    machine_active = any(e.get("active") for e in machine_envs)
    if machine_active:
        parts.append("*")

    # User layer
    user_envs = list_envs(Scope.USER, project_path)
    user_active = any(e.get("active") for e in user_envs)
    if user_active:
        parts.append("-")

    # Project layer
    config = _read_project_config(project_path)
    project_env = config.get("active_env") if config else None
    if project_env:
        parts.append(project_env)

    if not parts:
        return ""

    return f"[ip:{''.join(parts)}]"


def get_env_status(
    project_path: Path | None = None,
) -> list[dict[str, Any]]:
    """Get detailed status of active environments across all scopes.

    Returns a list of dicts: {scope, name, agent, path}.
    """
    if project_path is None:
        project_path = Path.cwd()

    result: list[dict[str, Any]] = []

    for scope in Scope:
        try:
            envs = list_envs(scope, project_path)
        except (ValueError, OSError):
            continue
        for env in envs:
            if env.get("active"):
                result.append({
                    "scope": scope.value,
                    "name": env.get("name", "unknown"),
                    "agent": env.get("agent", "unknown"),
                    "path": env.get("path", ""),
                })

    return result


def generate_activate_script(
    env_name: str,
    shell: str = "bash",
    prompt_tag: str = "",
) -> str:
    """Generate a shell script snippet for activation."""
    if not prompt_tag:
        prompt_tag = f"[ip:{env_name}]"
    if shell in ("bash", "zsh"):
        return _bash_activate_script(env_name, prompt_tag)
    if shell == "fish":
        return _fish_activate_script(env_name, prompt_tag)
    if shell in ("powershell", "pwsh"):
        return _powershell_activate_script(env_name, prompt_tag)
    return _bash_activate_script(env_name, prompt_tag)


def generate_deactivate_script(shell: str = "bash") -> str:
    """Generate a shell script snippet for deactivation."""
    if shell in ("bash", "zsh"):
        return _bash_deactivate_script()
    if shell == "fish":
        return _fish_deactivate_script()
    if shell in ("powershell", "pwsh"):
        return _powershell_deactivate_script()
    return _bash_deactivate_script()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _resolve_agent_config_dir(env_name: str, project_path: Path) -> str:
    """Resolve agent config dir name by searching env metadata across all scopes."""
    for scope in Scope:
        try:
            env_path = get_env_path(env_name, scope, project_path)
        except ValueError:
            continue
        meta_file = env_path / "env.yaml"
        if meta_file.exists():
            meta = yaml.safe_load(meta_file.read_text(encoding="utf-8")) or {}
            agent_name = meta.get("agent")
            if agent_name:
                from ipman.agents.registry import get_adapter
                return get_adapter(agent_name).config_dir_name
    return ".claude"  # fallback default


def _is_windows() -> bool:
    import sys
    return sys.platform == "win32"


def _write_env_metadata(
    env_path: Path, name: str, scope: Scope, adapter: AgentAdapter
) -> None:
    meta = {
        "name": name,
        "scope": scope.value,
        "agent": adapter.name,
        "created": datetime.now(tz=timezone.utc).isoformat(),
    }
    meta_file = env_path / "env.yaml"
    meta_file.write_text(yaml.dump(meta, default_flow_style=False), encoding="utf-8")


def _ensure_project_config(project_path: Path, adapter: AgentAdapter) -> None:
    """Create or update .ipman/ipman.yaml."""
    ipman_dir = get_project_ipman_dir(project_path)
    ipman_dir.mkdir(parents=True, exist_ok=True)
    config_file = ipman_dir / "ipman.yaml"
    if config_file.exists():
        return
    config = {
        "agent": adapter.name,
        "agent_config_dir": adapter.config_dir_name,
        "active_env": None,
    }
    content = yaml.dump(config, default_flow_style=False)
    config_file.write_text(content, encoding="utf-8")


def _read_project_config(project_path: Path) -> dict[str, Any] | None:
    config_file = get_project_ipman_dir(project_path) / "ipman.yaml"
    if not config_file.exists():
        return None
    return yaml.safe_load(config_file.read_text(encoding="utf-8")) or {}


def _update_project_config(project_path: Path, active_env: str | None) -> None:
    config_file = get_project_ipman_dir(project_path) / "ipman.yaml"
    config = yaml.safe_load(config_file.read_text(encoding="utf-8")) or {}
    config["active_env"] = active_env
    content = yaml.dump(config, default_flow_style=False)
    config_file.write_text(content, encoding="utf-8")


def _inherit_existing(
    adapter: AgentAdapter, env_path: Path, project_path: Path
) -> None:
    """Copy existing agent config into the new environment."""
    source = project_path / adapter.config_dir_name
    if not source.exists() or is_symlink(source):
        return
    # Copy contents (not the directory itself) into env_path
    for item in source.iterdir():
        dest = env_path / item.name
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dest)


def _bash_activate_script(env_name: str, prompt_tag: str) -> str:
    return f"""\
export IPMAN_ENV="{env_name}"
export _IPMAN_OLD_PS1="$PS1"
PS1="{prompt_tag} $PS1"
export PS1
"""


def _fish_activate_script(env_name: str, prompt_tag: str) -> str:
    return f"""\
set -gx IPMAN_ENV "{env_name}"
set -gx _IPMAN_OLD_PROMPT (functions fish_prompt)
function fish_prompt
    echo -n "{prompt_tag} "
    eval $_IPMAN_OLD_PROMPT
end
"""


def _powershell_activate_script(env_name: str, prompt_tag: str) -> str:
    return f"""\
$env:IPMAN_ENV = "{env_name}"
$_ipman_old_prompt = $function:prompt
function prompt {{ "{prompt_tag} " + (& $_ipman_old_prompt) }}
"""


def _bash_deactivate_script() -> str:
    return """\
if [ -n "$_IPMAN_OLD_PS1" ]; then
    PS1="$_IPMAN_OLD_PS1"
    export PS1
    unset _IPMAN_OLD_PS1
fi
unset IPMAN_ENV
"""


def _fish_deactivate_script() -> str:
    return """\
if set -q _IPMAN_OLD_PROMPT
    eval "function fish_prompt; $_IPMAN_OLD_PROMPT; end"
    set -e _IPMAN_OLD_PROMPT
end
set -e IPMAN_ENV
"""


def _powershell_deactivate_script() -> str:
    return """\
if ($null -ne $_ipman_old_prompt) {
    $function:prompt = $_ipman_old_prompt
    Remove-Variable _ipman_old_prompt
}
Remove-Item Env:IPMAN_ENV -ErrorAction SilentlyContinue
"""
