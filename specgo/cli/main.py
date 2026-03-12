# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""Typer-based CLI entrypoint.

Commands are registered via cli/commands/ modules.
"""

from __future__ import annotations

import typer


app = typer.Typer(
    add_completion=False,
    help="SpecGo: Spec-to-API toolchain for embedded protocols (scaffold).",
)


def _version_callback(value: bool) -> None:
    """Callback to print version and exit."""
    if value:
        from specgo import __version__
        typer.echo(__version__)
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False, "--version", help="Show version and exit.",
        callback=_version_callback, is_eager=True,
    ),
    global_scope: bool = typer.Option(
        False,
        "--global",
        "-g",
        help="Use global scope for commands that support it (e.g. `specgo -g config`).",
    ),
):
    """SpecGo CLI entrypoint."""
    ctx.ensure_object(dict)
    ctx.obj["global_scope"] = global_scope


@app.command("hello")
def hello():
    """A tiny smoke-test command."""
    typer.echo("SpecGo CLI is alive!")
