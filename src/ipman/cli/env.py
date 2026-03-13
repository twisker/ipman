"""CLI commands for virtual environment management."""

from __future__ import annotations

import os
from pathlib import Path

import click

from ipman.agents.registry import detect_agent, get_adapter, list_known_agents
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


def _resolve_scope(project: bool, user: bool, machine: bool) -> Scope:
    if user:
        return Scope.USER
    if machine:
        return Scope.MACHINE
    return Scope.PROJECT


def _resolve_adapter(agent: str | None, project_path: Path) -> object:
    """Resolve the agent adapter from --agent flag or auto-detection."""
    if agent:
        return get_adapter(agent)
    detected = detect_agent(project_path)
    if detected:
        return detected
    # Default to claude-code
    return get_adapter("claude-code")


def _detect_shell() -> str:
    shell_path = os.environ.get("SHELL", "")
    if "fish" in shell_path:
        return "fish"
    if "zsh" in shell_path or "bash" in shell_path:
        return "bash"
    # Windows
    if os.environ.get("PSMODULEPATH"):
        return "powershell"
    return "bash"


@click.group()
def env() -> None:
    """Manage virtual skill environments."""


@env.command()
@click.argument("name")
@click.option("--project", "scope_project", is_flag=True, default=True,
              help="Create in current project (default).")
@click.option("--user", "scope_user", is_flag=True, default=False,
              help="Create for current user.")
@click.option("--machine", "scope_machine", is_flag=True, default=False,
              help="Create for entire machine.")
@click.option("--agent", default=None,
              help=f"Agent tool to target. Known: {', '.join(list_known_agents())}")
@click.option("--inherit", is_flag=True, default=False,
              help="Inherit existing skills from current agent config.")
def create(
    name: str,
    scope_project: bool,
    scope_user: bool,
    scope_machine: bool,
    agent: str | None,
    inherit: bool,
) -> None:
    """Create a new virtual skill environment."""
    project_path = Path.cwd()
    scope = _resolve_scope(scope_project, scope_user, scope_machine)
    adapter = _resolve_adapter(agent, project_path)

    try:
        env_path = create_env(
            name=name,
            adapter=adapter,  # type: ignore[arg-type]
            scope=scope,
            project_path=project_path,
            inherit=inherit,
        )
        click.secho(
            f"Created environment '{name}' at {env_path}",
            fg="green",
        )
        click.echo(f"  Agent: {adapter.display_name}")  # type: ignore[attr-defined]
        click.echo(f"  Scope: {scope.value}")
        if inherit:
            click.echo("  Inherited existing skills.")
        click.echo(f"\nActivate with: ipman env activate {name}")
    except FileExistsError as e:
        click.secho(str(e), fg="red", err=True)
        raise SystemExit(1) from None


@env.command()
@click.argument("name")
@click.option("--project", "scope_project", is_flag=True, default=True)
@click.option("--user", "scope_user", is_flag=True, default=False)
@click.option("--machine", "scope_machine", is_flag=True, default=False)
def activate(
    name: str,
    scope_project: bool,
    scope_user: bool,
    scope_machine: bool,
) -> None:
    """Activate a virtual skill environment.

    To update your shell prompt, use:

        eval "$(ipman env activate myenv)"
    """
    project_path = Path.cwd()
    scope = _resolve_scope(scope_project, scope_user, scope_machine)

    try:
        env_path = activate_env(
            name=name,
            scope=scope,
            project_path=project_path,
        )
        shell = _detect_shell()
        script = generate_activate_script(name, shell)
        # If stdout is a terminal, print human-friendly message
        # If piped (eval), print only the script
        if os.isatty(1):
            click.secho(
                f"Activated environment '{name}' ({env_path})",
                fg="green",
            )
            click.echo(
                "\nTo update your shell prompt, run:\n"
                f'  eval "$(ipman env activate {name})"'
            )
        else:
            click.echo(script, nl=False)
    except (FileNotFoundError, FileExistsError) as e:
        click.secho(str(e), fg="red", err=True)
        raise SystemExit(1) from None


@env.command()
def deactivate() -> None:
    """Deactivate the current virtual skill environment.

    To update your shell prompt, use:

        eval "$(ipman env deactivate)"
    """
    project_path = Path.cwd()

    try:
        deactivate_env(project_path=project_path)
        shell = _detect_shell()
        script = generate_deactivate_script(shell)
        if os.isatty(1):
            click.secho("Environment deactivated.", fg="green")
            click.echo(
                "\nTo restore your shell prompt, run:\n"
                '  eval "$(ipman env deactivate)"'
            )
        else:
            click.echo(script, nl=False)
    except RuntimeError as e:
        click.secho(str(e), fg="red", err=True)
        raise SystemExit(1) from None


@env.command("delete")
@click.argument("name")
@click.option("--project", "scope_project", is_flag=True, default=True)
@click.option("--user", "scope_user", is_flag=True, default=False)
@click.option("--machine", "scope_machine", is_flag=True, default=False)
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation.")
def delete_cmd(
    name: str,
    scope_project: bool,
    scope_user: bool,
    scope_machine: bool,
    yes: bool,
) -> None:
    """Delete a virtual skill environment."""
    if not yes:
        click.confirm(
            f"Delete environment '{name}'? This cannot be undone.",
            abort=True,
        )

    project_path = Path.cwd()
    scope = _resolve_scope(scope_project, scope_user, scope_machine)

    try:
        delete_env(name=name, scope=scope, project_path=project_path)
        click.secho(f"Deleted environment '{name}'.", fg="green")
    except FileNotFoundError as e:
        click.secho(str(e), fg="red", err=True)
        raise SystemExit(1) from None


@env.command("list")
@click.option("--project", "scope_project", is_flag=True, default=True)
@click.option("--user", "scope_user", is_flag=True, default=False)
@click.option("--machine", "scope_machine", is_flag=True, default=False)
def list_cmd(
    scope_project: bool,
    scope_user: bool,
    scope_machine: bool,
) -> None:
    """List all virtual skill environments."""
    project_path = Path.cwd()
    scope = _resolve_scope(scope_project, scope_user, scope_machine)

    envs = list_envs(scope=scope, project_path=project_path)

    if not envs:
        click.echo(f"No environments found ({scope.value} scope).")
        return

    for e in envs:
        marker = click.style(" *", fg="cyan") if e.get("active") else ""
        name = e.get("name", "unknown")
        agent = e.get("agent", "unknown")
        created = e.get("created", "")
        click.echo(f"  {name}{marker}  (agent: {agent}, created: {created})")

    active_count = sum(1 for e in envs if e.get("active"))
    if active_count:
        click.echo("\n  * = currently active")
