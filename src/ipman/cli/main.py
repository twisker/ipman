"""IpMan CLI main entry point."""

import click

from ipman import __version__


@click.group()
@click.version_option(version=__version__, prog_name="ipman")
def cli() -> None:
    """IpMan - Intelligence Package Manager.

    Agent skill virtual environment manager.
    Create, manage, and share isolated skill environments
    for AI agent tools like Claude Code and OpenClaw.
    """


@cli.command()
def info() -> None:
    """Show IpMan installation info."""
    click.echo(f"IpMan v{__version__}")
    click.echo("https://github.com/twisker/ipman")
