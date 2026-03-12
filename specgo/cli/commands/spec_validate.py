# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""specgo validate — validate IR YAML files."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import typer

from specgo.cli.main import app


@app.command("validate")
@app.command("val")
def spec_validate(
    inputs: list[Path] = typer.Argument(..., help="One or more IR YAML files to validate."),
) -> None:
    """Validate IR files and write a report next to each input."""
    from specgo.ir.io import validate_input_paths, load_yaml, dump_yaml
    from specgo.ir.validator import validate_ir

    try:
        validate_input_paths(inputs)
    except (FileNotFoundError, ValueError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)

    for inp in inputs:
        if not inp.name.endswith(".ir.yaml"):
            typer.echo(
                f"Error: {inp} is not an .ir.yaml file. "
                f"Run 'specgo ingest' first to convert it.",
                err=True,
            )
            raise typer.Exit(code=1)

    has_errors = False

    for inp in inputs:
        typer.echo(f"Validating: {inp}")

        try:
            data = load_yaml(inp)
        except ValueError as e:
            typer.echo(f"  Error: {e}", err=True)
            has_errors = True
            continue

        # Run validation
        spec_ir, errors = validate_ir(data)

        # Build report
        report_path = inp.with_suffix(".validation.yaml")
        report = {
            "file": inp.name,
            "date": datetime.now().isoformat(),
            "source": str(inp),
            "result": "FAILED" if errors else "PASSED",
            "error_count": len(errors),
            "errors": errors if errors else [],
        }

        dump_yaml(report, report_path)

        if spec_ir is None:
            has_errors = True
            typer.echo("Error: IR validation failed due to schema errors.", err=True)

        if errors:
            has_errors = True
            typer.echo(f"  FAILED: {len(errors)} error(s)")
        else:
            typer.echo(f"  PASSED")

        typer.echo(f"  -> report: {report_path}")

    if has_errors:
        raise typer.Exit(code=1)

    typer.echo("Done.")
    raise typer.Exit(code=0)
