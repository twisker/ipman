"""IpMan CLI main entry point."""

import click

from ipman import __version__
from ipman.cli.env import env
from ipman.cli.hub import hub
from ipman.cli.init import init
from ipman.cli.pack import pack
from ipman.cli.skill import install, skill, uninstall
from ipman.utils.i18n import detect_locale, set_locale


@click.group()
@click.version_option(version=__version__, prog_name="ipman")
def cli() -> None:
    """IpMan - Intelligence Package Manager.

    Agent skill virtual environment manager.
    Create, manage, and share isolated skill environments
    for AI agent tools like Claude Code and OpenClaw.
    """
    set_locale(detect_locale())


cli.add_command(env)
cli.add_command(hub)
cli.add_command(init)
cli.add_command(pack)
cli.add_command(skill)
cli.add_command(install)
cli.add_command(uninstall)


@cli.command()
def info() -> None:
    """Show IpMan installation info."""
    click.echo(f"IpMan v{__version__}")
    click.echo("https://github.com/twisker/ipman")
