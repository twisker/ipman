"""CLI commands for IpHub (search, info, top, publish)."""

from __future__ import annotations

import click

from ipman.hub.client import IpHubClient


def _get_hub_client() -> IpHubClient:
    """Create a default IpHubClient instance."""
    return IpHubClient()


@click.group()
def hub() -> None:
    """Browse and publish to the IpHub registry."""


@hub.command()
@click.argument("query", default="")
@click.option("--agent", default=None, help="Filter by agent (e.g. claude-code).")
def search(query: str, agent: str | None) -> None:
    """Search IpHub for skills and packages."""
    client = _get_hub_client()
    results = client.search(query, agent=agent)

    if not results:
        click.echo("No results found.")
        return

    for r in results:
        rtype = r.get("type", "skill")
        tag = click.style(f"[{rtype}]", fg="cyan")
        name = click.style(r["name"], bold=True)
        desc = r.get("description", "")
        installs = r.get("installs", 0)
        click.echo(f"  {tag} {name}  {desc}  ({installs} installs)")


@hub.command()
@click.argument("name")
def info(name: str) -> None:
    """Show detailed info for a skill or package."""
    client = _get_hub_client()
    entry = client.lookup(name)

    if entry is None:
        raise click.ClickException(f"'{name}' not found in IpHub.")

    click.secho(entry["name"], bold=True)
    click.echo(f"  Type:        {entry.get('type', 'skill')}")
    click.echo(f"  Owner:       {entry.get('owner', 'unknown')}")
    click.echo(f"  Description: {entry.get('description', '')}")

    if entry.get("latest"):
        click.echo(f"  Latest:      {entry['latest']}")
    if entry.get("versions"):
        click.echo(f"  Versions:    {', '.join(entry['versions'])}")
    if entry.get("agents"):
        click.echo(f"  Agents:      {', '.join(entry['agents'])}")

    installs = entry.get("installs", 0)
    users = entry.get("unique_users", 0)
    click.echo(f"  Installs:    {installs} ({users} unique users)")


@hub.command()
@click.option("--limit", "-n", default=10, help="Number of entries to show.")
def top(limit: int) -> None:
    """Show most installed skills and packages."""
    client = _get_hub_client()
    index = client.fetch_index()

    entries: list[dict] = []
    for section in ("skills", "packages"):
        items = index.get(section, {})
        for name, data in items.items():
            entries.append({"name": name, **data})

    entries.sort(key=lambda e: e.get("installs", 0), reverse=True)

    if not entries:
        click.echo("No entries in IpHub.")
        return

    click.secho("IpHub Top:", bold=True)
    for i, e in enumerate(entries[:limit], 1):
        rtype = e.get("type", "skill")
        tag = click.style(f"[{rtype}]", fg="cyan")
        name = click.style(e["name"], bold=True)
        installs = e.get("installs", 0)
        click.echo(f"  {i}. {tag} {name}  ({installs} installs)")
