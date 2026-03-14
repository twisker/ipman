"""CLI commands for skill management (delegated to agent CLI)."""

from __future__ import annotations

from pathlib import Path

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


def _is_ip_file(source: str) -> bool:
    """Check if the source argument looks like an .ip.yaml file path."""
    return source.endswith(".ip.yaml")


def _install_from_ip_file(
    path: Path, adapter: AgentAdapter, *, dry_run: bool = False,
) -> None:
    """Install all skills from an .ip.yaml file."""
    from ipman.core.package import parse_ip_file

    if not path.exists():
        raise click.ClickException(f"IP file not found: {path}")

    pkg = parse_ip_file(path)

    if not pkg.skills:
        click.secho(
            f"No skills defined in {path.name} — nothing to install.",
            fg="yellow",
        )
        return

    if dry_run:
        click.echo(f"Would install {len(pkg.skills)} skill(s) from {path.name}:")
        for s in pkg.skills:
            click.echo(f"  {s.name}")
        return

    ok, failed = 0, 0
    for s in pkg.skills:
        result = adapter.install_skill(s.name)
        if result.returncode == 0:
            click.secho(f"  Installed '{s.name}'", fg="green")
            ok += 1
        else:
            msg = result.stderr.strip() or result.stdout.strip() or "Unknown error"
            click.secho(f"  Failed '{s.name}': {msg}", fg="red", err=True)
            failed += 1

    click.echo(f"\n{ok} installed, {failed} failed (from {path.name})")
    if failed:
        raise SystemExit(1)


@click.command()
@click.argument("source")
@click.option("--agent", "agent_name", default=None,
              help="Agent tool to use (e.g. claude-code, openclaw).")
@click.option("--dry-run", is_flag=True, default=False,
              help="Show what would be installed without executing.")
def install(source: str, agent_name: str | None, dry_run: bool) -> None:
    """Install a skill or an IP package.

    SOURCE can be a skill name (e.g. web-scraper) or an .ip.yaml file path.
    """
    adapter = _resolve_agent(agent_name)

    if _is_ip_file(source):
        _install_from_ip_file(Path(source), adapter, dry_run=dry_run)
        return

    # Single skill install (original behavior)
    if dry_run:
        click.echo(f"Would install skill: {source}")
        return

    result = adapter.install_skill(source)
    if result.returncode == 0:
        click.secho(
            f"Installed '{source}' via {adapter.display_name}.",
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
