# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""specgo run — execute the full agent pipeline.

This command is the main entry point for running the end-to-end SpecGo pipeline, including:
- Spec import and validation
- Agent execution to generate code and artifacts
- Differential testing against golden models
- Report generation
- Iteration
"""

from __future__ import annotations

from pathlib import Path

import typer

from specgo.cli.default_paths import DEFAULT_OUTPUT_ROOT
from specgo.cli.main import app


@app.command("run")
@app.command("go")
def cli_run(
    spec: list[Path] = typer.Argument(..., help="One or more spec files to process."),
    workspace: Path = typer.Option(DEFAULT_OUTPUT_ROOT, "--workspace", "-w", help="Workspace root directory."),
    force: bool = typer.Option(
        False, "--force", "-f", help="Overwrite existing outputs."
    ),
) -> None:
    """Run the full spec-to-API agent pipeline.

    TODO: Implement end-to-end pipeline orchestration.
    """
    typer.echo(f"Workspace: {workspace}")
    for s in spec:
        if not s.exists():
            typer.echo(f"Error: Spec file does not exist: {s}", err=True)
            raise typer.Exit(code=1)
        typer.echo(f"  spec: {s}")

    # TODO: call agent runner
    typer.echo("TODO: pipeline execution not implemented")
    raise typer.Exit(code=0)
