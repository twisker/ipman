"""IpMan CLI main entry point."""

import click

from ipman import __version__
from ipman.cli.env import env
from ipman.cli.hub import hub
from ipman.cli.init import init
from ipman.cli.pack import pack
from ipman.cli.passthrough import create_passthrough_group
from ipman.cli.skill import install, list_cmd, uninstall
from ipman.utils.i18n import detect_locale, set_locale

SKILLS_CMD_MAP = {
    "claude-code": ["claude", "plugin"],
    "openclaw": ["openclaw", "skills"],
}

PLUGINS_CMD_MAP = {
    "claude-code": ["claude", "plugin"],
    "openclaw": ["openclaw", "plugins"],
}


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
# Create passthrough groups
skills_group = create_passthrough_group(
    name="skills",
    help="Manage skills in the current environment.",
    agent_cmd_map=SKILLS_CMD_MAP,
)
skills_group.add_command(list_cmd, "list")

plugins_group = create_passthrough_group(
    name="plugins",
    help="Manage plugins/extensions in the current environment.",
    agent_cmd_map=PLUGINS_CMD_MAP,
)

# Register groups + aliases
cli.add_command(skills_group, "skills")
cli.add_command(skills_group, "skill")
cli.add_command(plugins_group, "plugins")
cli.add_command(plugins_group, "plugin")

# Keep top-level install/uninstall
cli.add_command(install)
cli.add_command(uninstall)


@cli.command()
def info() -> None:
    """Show IpMan installation info."""
    click.echo(f"IpMan v{__version__}")
    click.echo("https://github.com/twisker/ipman")
