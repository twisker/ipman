"""CLI commands for skill management (delegated to agent CLI)."""

from __future__ import annotations

import click

from ipman.agents.base import AgentAdapter
from ipman.agents.registry import detect_agent, get_adapter


def _resolve_agent(agent_name: str | None) -> AgentAdapter:
    """Resolve adapter from --agent flag or auto-detection."""
    if agent_name:
        return get_adapter(agent_name)
    detected = detect_agent()
    if detected is None:
        raise click.ClickException(
            "No agent detected. Use --agent to specify one "
            "(e.g. --agent claude-code)."
        )
    return detected


@click.command()
@click.argument("name")
@click.option("--agent", "agent_name", default=None,
              help="Agent tool to use (e.g. claude-code, openclaw).")
def install(name: str, agent_name: str | None) -> None:
    """Install a skill via the agent's native CLI."""
    adapter = _resolve_agent(agent_name)
    result = adapter.install_skill(name)
    if result.returncode == 0:
        click.secho(
            f"Installed '{name}' via {adapter.display_name}.",
            fg="green",
        )
        if result.stdout.strip():
            click.echo(result.stdout.strip())
    else:
        msg = result.stderr.strip() or result.stdout.strip() or "Unknown error"
        click.secho(f"Install failed: {msg}", fg="red", err=True)
        raise SystemExit(1)


@click.command()
@click.argument("name")
@click.option("--agent", "agent_name", default=None,
              help="Agent tool to use (e.g. claude-code, openclaw).")
def uninstall(name: str, agent_name: str | None) -> None:
    """Uninstall a skill via the agent's native CLI."""
    adapter = _resolve_agent(agent_name)
    result = adapter.uninstall_skill(name)
    if result.returncode == 0:
        click.secho(
            f"Uninstalled '{name}' via {adapter.display_name}.",
            fg="green",
        )
    else:
        msg = result.stderr.strip() or result.stdout.strip() or "Unknown error"
        click.secho(f"Uninstall failed: {msg}", fg="red", err=True)
        raise SystemExit(1)


@click.group()
def skill() -> None:
    """Manage skills in the current environment."""


@skill.command("list")
@click.option("--agent", "agent_name", default=None,
              help="Agent tool to use (e.g. claude-code, openclaw).")
def list_cmd(agent_name: str | None) -> None:
    """List installed skills via the agent's native CLI."""
    adapter = _resolve_agent(agent_name)
    skills = adapter.list_skills()
    if not skills:
        click.echo(f"No skills installed ({adapter.display_name}).")
        return
    for s in skills:
        status = "" if s.enabled else click.style(" (disabled)", fg="yellow")
        version = f" v{s.version}" if s.version else ""
        click.echo(f"  {s.name}{version}{status}")
    click.echo(f"\n{len(skills)} skill(s) installed.")
