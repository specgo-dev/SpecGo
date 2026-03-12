# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""specgo proto-codegen — generate protocol code from IR."""

from __future__ import annotations

from pathlib import Path

import typer

from specgo.cli.default_paths import DEFAULT_GEN_DIR
from specgo.cli.main import app


@app.command("proto-codegen")
@app.command("gen")
def cli_protocol_codegen(
    ir: Path = typer.Argument(..., help="Input validated IR YAML file."),
    output: Path = typer.Option(DEFAULT_GEN_DIR, "--out", "-o", help="Output directory for generated code."),
    lang: str = typer.Option("c", "--lang", help="Target language (currently only c)."),
) -> None:
    """Generate protocol encoder/decoder code from a validated IR file."""
    from specgo.ir.io import validate_input_paths, validate_output_dir, load_ir
    from specgo.codegen.protocol import generate_protocol

    try:
        validate_input_paths([ir])
    except (FileNotFoundError, ValueError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)

    try:
        spec_ir = load_ir(ir)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)

    try:
        validate_output_dir(output)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)

    try:
        generated_files = generate_protocol(spec_ir, str(output), lang=lang)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)

    typer.echo("Generated files:")
    for file_path in generated_files:
        typer.echo(f"  - {file_path}")

    raise typer.Exit(code=0)
