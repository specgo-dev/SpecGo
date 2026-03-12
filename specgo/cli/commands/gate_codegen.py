# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""specgo gate-codegen — evaluate gates for generated C/H code."""

from __future__ import annotations

import sys
from pathlib import Path

import typer

from specgo.cli.default_paths import DEFAULT_GEN_DIR
from specgo.cli.main import app


@app.command("gate-codegen")
@app.command("gate")
def cli_gate_codegen(
    ir: Path = typer.Argument(..., help="Input IR YAML file."),
    gen_dir: Path = typer.Option(DEFAULT_GEN_DIR, "--gen", "-g", help="Directory with generated C/H files."),
    lang: str = typer.Option("c", "--lang", help="Target language (currently only c)."),
    compile_check: bool = typer.Option(
        True,
        "--compile-check/--no-compile-check",
        help="Enable C syntax compile gate.",
    ),
    compiler: str = typer.Option(
        "cl" if sys.platform == "win32" else "cc",
        "--compiler",
        help="Compiler command for syntax gate.",
    ),
) -> None:
    """Run codegen gates on generated protocol C/H files."""
    from specgo.gates.codegen import render_codegen_gate_report, run_codegen_gates
    from specgo.gates.evaluator import evaluate_codegen
    from specgo.gates.io import load_validated_ir, validate_existing_codegen_dir

    try:
        spec_ir = load_validated_ir(ir)
    except (FileNotFoundError, ValueError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)

    try:
        validate_existing_codegen_dir(gen_dir)
    except (FileNotFoundError, ValueError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)

    metrics = run_codegen_gates(
        spec_ir,
        ir,
        gen_dir,
        lang=lang,
        compile_check=compile_check,
        compiler=compiler,
    )
    typer.echo(render_codegen_gate_report(metrics))

    if not evaluate_codegen(metrics):
        raise typer.Exit(code=1)
    
    raise typer.Exit(code=0)
