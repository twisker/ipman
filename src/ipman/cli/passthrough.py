"""Passthrough Click group that delegates unknown subcommands to agent CLI."""
from __future__ import annotations

from pathlib import Path

import click

from ipman.cli._common import resolve_agent
from ipman.core.environment import symlink_guard


class AgentPassthroughGroup(click.Group):
    """Click group that passes unrecognized subcommands to agent CLI.

    Known subcommands (registered via @group.command) are handled
    normally. Unknown subcommands are forwarded to the agent's native
    CLI using the configured command prefix mapping.
    """

    def __init__(
        self,
        *args,
        agent_cmd_map: dict[str, list[str]],
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.agent_cmd_map = agent_cmd_map

    def resolve_command(self, ctx, args):
        """Try normal resolution first; fall back to passthrough."""
        try:
            cmd_name, cmd, remaining = super().resolve_command(ctx, args)
            if cmd is not None:
                return cmd_name, cmd, remaining
        except click.UsageError:
            pass
        # Unknown command -> passthrough
        return "_passthrough", self.commands["_passthrough"], args

    def parse_args(self, ctx, args):
        """Extract --agent before normal parsing."""
        agent_name = None
        filtered = []
        skip_next = False
        for i, arg in enumerate(args):
            if skip_next:
                skip_next = False
                continue
            if arg == "--agent" and i + 1 < len(args):
                agent_name = args[i + 1]
                skip_next = True
            elif arg.startswith("--agent="):
                agent_name = arg.split("=", 1)[1]
            else:
                filtered.append(arg)
        ctx.ensure_object(dict)
        ctx.obj["agent_name"] = agent_name
        return super().parse_args(ctx, filtered)

    def format_help(self, ctx, formatter):
        """Show ipman commands, then hint about agent passthrough."""
        super().format_help(ctx, formatter)
        formatter.write("\n")
        formatter.write(
            "  Unrecognized subcommands are passed through to the agent CLI.\n"
            "  Use --agent to specify the agent (or auto-detected).\n"
        )


def _make_passthrough_cmd(agent_cmd_map: dict[str, list[str]]) -> click.Command:
    """Create the hidden _passthrough command."""

    @click.command("_passthrough", hidden=True)
    @click.argument("args", nargs=-1, type=click.UNPROCESSED)
    @click.pass_context
    def _passthrough(ctx, args):
        agent_name = ctx.obj.get("agent_name") if ctx.obj else None
        adapter = resolve_agent(agent_name)

        prefix = agent_cmd_map.get(adapter.name)
        if not prefix:
            raise click.ClickException(
                f"Agent '{adapter.name}' is not supported by this command."
            )

        full_cmd = prefix + list(args)
        project_path = Path.cwd()

        with symlink_guard(project_path):
            result = adapter._run_cli(full_cmd)

        if result.stdout:
            click.echo(result.stdout, nl=False)
        if result.stderr:
            click.echo(result.stderr, nl=False, err=True)
        ctx.exit(result.returncode)

    return _passthrough


def create_passthrough_group(
    name: str,
    help: str,
    agent_cmd_map: dict[str, list[str]],
) -> AgentPassthroughGroup:
    """Factory: create a passthrough group with its hidden _passthrough command."""
    group = AgentPassthroughGroup(
        name=name,
        help=help,
        agent_cmd_map=agent_cmd_map,
    )
    group.add_command(_make_passthrough_cmd(agent_cmd_map))
    return group
