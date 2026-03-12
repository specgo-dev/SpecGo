# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""specgo ingest — import spec files and generate IR."""

from __future__ import annotations

from pathlib import Path

import typer

from specgo.cli.default_paths import DEFAULT_IR_DIR
from specgo.cli.main import app


@app.command("ingest")
@app.command("ing")
def cli_spec_ingest(
    force: bool = typer.Option(
        False, "--force", "-f", help="Overwrite existing files or create missing directories."
    ),
    spec: list[Path] = typer.Argument(..., help="One or more input spec file paths."),
    output: Path | None = typer.Option(
        None, "--out", "-o", help="Output IR file or directory path."
    ),
) -> None:
    """Ingest spec files and generate IR."""
    # Ingest the functions here
    from specgo.ingest.dispatcher import spec_dispatch
    from specgo.ir.io import (
        validate_input_paths, validate_output_path,
        resolve_output_file, dump_ir,
    )

    try:
        validate_input_paths(spec)
    except (FileNotFoundError, ValueError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)

    if output is None:
        # Default output layout under ./specgo_output/output
        output = DEFAULT_IR_DIR
        output.mkdir(parents=True, exist_ok=True)

    try:
        validate_output_path(output, len(spec), force)
    except (FileExistsError, FileNotFoundError, ValueError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)

    for inp in spec:
        typer.echo(f"Importing: {inp}")
        try:
            ir_data = spec_dispatch(inp)
        except ValueError as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(code=1)

        out_file = resolve_output_file(inp, output)
        dump_ir(ir_data, out_file)
        typer.echo(f"  -> wrote: {out_file}")

    typer.echo("Done.")
    raise typer.Exit(code=0)
