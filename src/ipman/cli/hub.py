"""CLI commands for IpHub (search, info, top, publish)."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import click

from ipman.core.vetter import RiskLevel, assess_risk, vet_skill_content
from ipman.hub.client import IpHubClient
from ipman.hub.publisher import IpHubPublisher, PublishError, get_github_username


def _submit_report(
    name: str, body: str,
) -> subprocess.CompletedProcess[str]:
    """Submit a report issue to IpHub via gh CLI."""
    import subprocess as _sp
    return _sp.run(
        [
            "gh", "issue", "create",
            "--repo", "twisker/iphub",
            "--title", f"[report] {name}",
            "--body", body,
            "--label", "report",
        ],
        capture_output=True, text=True, check=False,
    )


def _get_hub_client() -> IpHubClient:
    """Create an IpHubClient using configured hub URL."""
    from ipman.core.config import load_config
    cfg = load_config()
    return IpHubClient(base_url=cfg.hub_url)


@click.group()
def hub() -> None:
    """Browse and publish to the IpHub registry."""


@hub.command()
@click.argument("query", default="")
@click.option("--agent", default=None, help="Filter by agent (e.g. claude-code).")
@click.option("--tag", default=None, help="Filter by tag (e.g. frontend).")
def search(query: str, agent: str | None, tag: str | None) -> None:
    """Search IpHub for skills and packages."""
    client = _get_hub_client()
    results = client.search(query, agent=agent, tag=tag)

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

    if entry.get("tags"):
        click.echo(f"  Tags:        {', '.join(entry['tags'])}")
    if entry.get("summary"):
        click.echo(f"  Summary:     {entry['summary'].strip()}")
    if entry.get("homepage"):
        click.echo(f"  Homepage:    {entry['homepage']}")
    if entry.get("repository"):
        click.echo(f"  Repository:  {entry['repository']}")
    if entry.get("links"):
        click.echo("  Links:")
        for link in entry["links"]:
            click.echo(f"    - {link.get('title', '')}: {link.get('url', '')}")


@hub.command()
@click.option("--limit", "-n", default=10, help="Number of entries to show.")
@click.option("--tag", default=None, help="Filter by tag.")
def top(limit: int, tag: str | None) -> None:
    """Show most installed skills and packages."""
    client = _get_hub_client()
    index = client.fetch_index()

    entries: list[dict[str, Any]] = []
    for section in ("skills", "packages"):
        items = index.get(section, {})
        for name, data in items.items():
            entries.append({"name": name, **data})

    entries.sort(key=lambda e: e.get("installs", 0), reverse=True)

    if tag:
        entries = [e for e in entries if tag in e.get("tags", [])]

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


@hub.command()
@click.argument("source")
@click.option("--description", "-d", default="", help="Skill/package description.")
@click.option("--license", "license_", default=None, help="License (e.g. MIT).")
@click.option("--homepage", default=None, help="Project homepage URL.")
def publish(
    source: str, description: str,
    license_: str | None, homepage: str | None,
) -> None:
    """Publish a skill or IP package to IpHub.

    SOURCE can be a skill name (e.g. web-scraper) or an .ip.yaml file path.
    """
    try:
        username = get_github_username()
    except PublishError as e:
        raise click.ClickException(str(e)) from e

    publisher = IpHubPublisher(username=username)

    if source.endswith(".ip.yaml"):
        # Publish IP package
        path = Path(source)
        if not path.exists():
            raise click.ClickException(f"File not found: {source}")

        from ipman.core.package import parse_ip_file
        pkg = parse_ip_file(path)

        # Pre-publish risk assessment
        content = path.read_text(encoding="utf-8")
        flags = vet_skill_content(content)
        report = assess_risk(flags, skill_name=pkg.name)
        if report.risk_level >= RiskLevel.HIGH:
            click.secho(
                f"Publish blocked: '{pkg.name}' rated "
                f"{report.risk_level.name}",
                fg="red", err=True,
            )
            for f in report.flags:
                click.secho(f"  {f.description}", fg="red", err=True)
            raise click.ClickException(
                "HIGH/EXTREME risk items cannot be published."
            )

        vet_summary = "\n".join(
            f"- {f.description}" for f in report.flags
        ) if report.flags else "No issues detected."

        click.echo(
            f"Publishing package '{pkg.name}' v{pkg.version} "
            f"as @{username} (risk: {report.risk_level.name})...",
        )
        try:
            pr_url = publisher.publish_package(
                pkg,
                risk_level=report.risk_level.name,
                vet_summary=vet_summary,
            )
        except PublishError as e:
            raise click.ClickException(str(e)) from e
        click.secho(f"PR created: {pr_url}", fg="green")
    else:
        # Publish skill
        if not description:
            raise click.ClickException(
                "Description is required for skill publishing. "
                "Use --description."
            )

        # Pre-publish risk assessment on description
        flags = vet_skill_content(description)
        report = assess_risk(flags, skill_name=source)
        if report.risk_level >= RiskLevel.HIGH:
            click.secho(
                f"Publish blocked: '{source}' rated "
                f"{report.risk_level.name}",
                fg="red", err=True,
            )
            for f in report.flags:
                click.secho(f"  {f.description}", fg="red", err=True)
            raise click.ClickException(
                "HIGH/EXTREME risk items cannot be published."
            )

        vet_summary = "\n".join(
            f"- {f.description}" for f in report.flags
        ) if report.flags else "No issues detected."

        click.echo(
            f"Publishing skill '{source}' as @{username} "
            f"(risk: {report.risk_level.name})...",
        )
        try:
            pr_url = publisher.publish_skill(
                name=source,
                description=description,
                license_=license_,
                homepage=homepage,
                risk_level=report.risk_level.name,
                vet_summary=vet_summary,
            )
        except PublishError as e:
            raise click.ClickException(str(e)) from e
        click.secho(f"PR created: {pr_url}", fg="green")


@hub.command("report")
@click.argument("name")
@click.option("--reason", "-r", required=True,
              help="Reason for reporting (required).")
def report_cmd(name: str, reason: str) -> None:
    """Report a suspicious skill or package."""
    try:
        username = get_github_username()
    except PublishError as e:
        raise click.ClickException(str(e)) from e

    client = _get_hub_client()
    entry = client.lookup(name)
    if entry is None:
        raise click.ClickException(f"'{name}' not found in IpHub.")

    body = f"Report by @{username}: {reason}"
    result = _submit_report(name, body)
    if result.returncode != 0:
        msg = result.stderr.strip() or "Failed to submit report"
        raise click.ClickException(msg)

    click.secho(
        f"Reported '{name}'. Thank you for helping keep "
        f"IpHub safe.",
        fg="green",
    )
