"""CLI command: ipman init — shell integration setup."""

from __future__ import annotations

import click

from ipman.core.shell_init import (
    SUPPORTED_SHELLS,
    config_file_path,
    detect_shell,
    generate_injection,
    inject_into_file,
    remove_from_file,
)


@click.command("init")
@click.argument("shells", nargs=-1)
@click.option("--reverse", is_flag=True, help="Remove ipman shell integration.")
@click.option("--dry-run", is_flag=True, help="Print injection without writing.")
def init(shells: tuple[str, ...], reverse: bool, dry_run: bool) -> None:
    """Set up shell integration for ipman.

    Injects a shell function wrapper into your shell config file so that
    commands like ``ipman env activate`` work correctly.

    If no SHELLS are specified, the current shell is auto-detected.
    """
    if not shells:
        shells = (detect_shell(),)

    for shell in shells:
        if shell not in SUPPORTED_SHELLS:
            click.secho(f"Unknown shell: {shell}", fg="red")
            continue

        cfg = config_file_path(shell)

        if dry_run:
            injection = generate_injection(shell)
            click.echo(f"Shell:  {shell}")
            click.echo(f"Config: {cfg}")
            click.echo(injection)
            continue

        if reverse:
            removed = remove_from_file(cfg)
            if removed:
                click.echo(f"Removed ipman integration from {cfg}")
            else:
                click.echo(f"No ipman integration found in {cfg}")
            continue

        inject_into_file(cfg, shell)
        click.echo(f"Injected ipman integration into {cfg}")
        click.echo(f"Run: source {cfg}")
