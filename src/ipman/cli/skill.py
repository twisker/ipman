"""CLI commands for skill management (delegated to agent CLI)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import click

from ipman.agents.base import AgentAdapter
from ipman.cli._common import resolve_agent as _resolve_agent
from ipman.core.config import SecurityMode, load_config
from ipman.core.security import Action, decide_action, log_security_event
from ipman.core.vetter import RiskLevel, VetReport, assess_risk, vet_skill_content

if TYPE_CHECKING:
    from ipman.hub.client import IpHubClient


def _is_ip_file(source: str) -> bool:
    """Check if the source argument looks like an .ip.yaml file path."""
    return source.endswith(".ip.yaml")


def _run_vet(content: str, skill_name: str) -> VetReport:
    """Run risk assessment on skill content."""
    flags = vet_skill_content(content)
    return assess_risk(flags, skill_name=skill_name)


def _enforce_security(
    report: VetReport,
    mode: SecurityMode,
    source: str,
) -> bool:
    """Enforce security policy. Returns True if install should proceed."""
    action = decide_action(report.risk_level, mode)
    cfg = load_config()

    if action == Action.BLOCK:
        click.secho(
            f"BLOCKED: '{report.skill_name}' — "
            f"risk {report.risk_level.name}",
            fg="red", err=True,
        )
        for f in report.flags:
            click.secho(f"  {f.description}", fg="red", err=True)
        if cfg.log_enabled:
            log_security_event(
                log_path=cfg.log_path,
                skill_name=report.skill_name,
                source=source,
                risk_level=report.risk_level,
                action=action,
            )
        return False

    if action in (Action.WARN_INSTALL, Action.WARN_CONFIRM):
        click.secho(
            f"WARNING: '{report.skill_name}' — "
            f"risk {report.risk_level.name}",
            fg="yellow", err=True,
        )
        for f in report.flags:
            click.secho(f"  {f.description}", fg="yellow", err=True)
        if cfg.log_enabled:
            log_security_event(
                log_path=cfg.log_path,
                skill_name=report.skill_name,
                source=source,
                risk_level=report.risk_level,
                action=action,
            )

    return True


def _get_hub_client() -> IpHubClient:
    """Create an IpHubClient using configured hub URL."""
    from ipman.hub.client import IpHubClient
    cfg = load_config()
    return IpHubClient(base_url=cfg.hub_url)


def _install_from_hub(
    name: str, adapter: AgentAdapter, *, dry_run: bool = False,
) -> None:
    """Install a skill or IP package by short name via IpHub."""
    hub = _get_hub_client()
    info = hub.lookup(name)
    if info is None:
        raise click.ClickException(
            f"'{name}' not found in IpHub. "
            "Check the name or use a file path for local .ip.yaml files."
        )

    entry_type = info.get("type", "skill")

    if entry_type == "skill":
        if dry_run:
            click.echo(f"Would install skill: {name} (from IpHub)")
            return
        result = adapter.install_skill(name)
        if result.returncode == 0:
            click.secho(f"Installed '{name}' via {adapter.display_name}.", fg="green")
        else:
            msg = result.stderr.strip() or result.stdout.strip() or "Unknown error"
            click.secho(f"Install failed: {msg}", fg="red", err=True)
            raise SystemExit(1)
    else:
        # IP package — fetch version file and install all skills
        registry = hub.fetch_registry(name)
        if registry is None:
            raise click.ClickException(f"Failed to fetch registry for '{name}'.")

        skills = registry.get("skills", [])
        if not skills:
            click.secho(f"No skills in package '{name}'.", fg="yellow")
            return

        if dry_run:
            click.echo(f"Would install {len(skills)} skill(s) from package '{name}':")
            for s in skills:
                click.echo(f"  {s['name']}")
            return

        ok, failed = 0, 0
        for s in skills:
            r = adapter.install_skill(s["name"])
            if r.returncode == 0:
                click.secho(f"  Installed '{s['name']}'", fg="green")
                ok += 1
            else:
                msg = r.stderr.strip() or r.stdout.strip() or "Unknown error"
                click.secho(f"  Failed '{s['name']}': {msg}", fg="red", err=True)
                failed += 1

        click.echo(f"\n{ok} installed, {failed} failed (from package '{name}')")
        if failed:
            raise SystemExit(1)


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
@click.option("--security", "security_mode", default=None,
              type=click.Choice(
                  ["permissive", "default", "cautious", "strict"],
                  case_sensitive=False,
              ),
              help="Security mode override.")
@click.option("--vet", "force_vet", is_flag=True, default=False,
              help="Force local risk assessment (even for IpHub).")
@click.option("--no-vet", "skip_vet", is_flag=True, default=False,
              help="Skip local risk assessment.")
@click.option("--yes", "auto_yes", is_flag=True, default=False,
              help="Auto-confirm security warnings.")
def install(
    source: str,
    agent_name: str | None,
    dry_run: bool,
    security_mode: str | None,
    force_vet: bool,
    skip_vet: bool,
    auto_yes: bool,
) -> None:
    """Install a skill or an IP package.

    SOURCE can be a skill name (e.g. web-scraper) or an .ip.yaml file path.
    """
    adapter = _resolve_agent(agent_name)

    # Resolve security mode
    cfg = load_config()
    mode = SecurityMode(security_mode) if security_mode else cfg.security_mode

    is_local = _is_ip_file(source)

    # Determine whether to run local vet
    should_vet = False
    if skip_vet:
        should_vet = False
    elif force_vet:
        should_vet = True
    elif is_local:
        # Local/URL sources: always vet by default
        should_vet = True
    elif mode == SecurityMode.STRICT:
        # STRICT mode: vet everything
        should_vet = True
    # else: IpHub source in non-STRICT mode → trust existing label

    # Run vet if needed
    if should_vet and not dry_run:
        if is_local:
            path = Path(source)
            if not path.exists():
                raise click.ClickException(
                    f"IP file not found: {path}",
                )
            content = path.read_text(encoding="utf-8")
            report = _run_vet(content, skill_name=source)
        else:
            # For hub skills, vet the registry content
            report = _run_vet("", skill_name=source)

        if not _enforce_security(report, mode, source):
            raise SystemExit(1)

    if is_local:
        _install_from_ip_file(
            Path(source), adapter, dry_run=dry_run,
        )
    else:
        _install_from_hub(source, adapter, dry_run=dry_run)


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
