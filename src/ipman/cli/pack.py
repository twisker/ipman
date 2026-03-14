"""CLI command for packing the current environment into an .ip.yaml file."""

from __future__ import annotations

from pathlib import Path

import click

from ipman.cli._common import resolve_agent as _resolve_agent
from ipman.core.package import IPPackage, SkillRef, dump_ip_file


@click.command()
@click.option("--name", "-n", required=True,
              help="Package name for the .ip.yaml file.")
@click.option("--version", "-v", "pkg_version", default="1.0.0",
              help="Package version (default: 1.0.0).")
@click.option("--description", "-d", default="",
              help="Package description.")
@click.option("--output", "-o", "output_path", default=None,
              type=click.Path(),
              help="Output file path (default: <name>.ip.yaml).")
@click.option("--agent", "agent_name", default=None,
              help="Agent tool to use (e.g. claude-code, openclaw).")
@click.option("--force", is_flag=True, default=False,
              help="Overwrite existing output file.")
def pack(
    name: str,
    pkg_version: str,
    description: str,
    output_path: str | None,
    agent_name: str | None,
    force: bool,
) -> None:
    """Pack current environment skills into an .ip.yaml file.

    Reads installed skills from the active agent and generates
    a distributable IP package file.
    """
    adapter = _resolve_agent(agent_name)

    # Determine output path
    out = Path(output_path) if output_path else Path(f"{name}.ip.yaml")

    if out.exists() and not force:
        raise click.ClickException(
            f"Output file already exists: {out}\n"
            "Use --force to overwrite."
        )

    # Read skills from agent
    skills_info = adapter.list_skills()
    skill_refs = [
        SkillRef(name=s.name, version=s.version or None)
        for s in skills_info
    ]

    pkg = IPPackage(
        name=name,
        version=pkg_version,
        description=description,
        skills=skill_refs,
    )

    dump_ip_file(pkg, out)

    click.secho(
        f"Packed {len(skill_refs)} skill(s) into {out}",
        fg="green",
    )
