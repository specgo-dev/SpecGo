# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""specgo test-diff — run differential tests."""

from __future__ import annotations

from pathlib import Path

import typer

from specgo.cli.default_paths import DEFAULT_GEN_DIR, DEFAULT_IR_DIR, DEFAULT_REPORTS_DIR
from specgo.cli.main import app


@app.command("test-diff")
@app.command("diff")
def cli_test_diff(
    spec: Path | None = typer.Option(
        None,
        "--ir",
        "-i",
        help="IR file for the spec under test. If omitted, auto-picks first *.ir.yaml under specgo_output/output.",
    ),
    gen_dir: Path = typer.Option(DEFAULT_GEN_DIR, "--gen", help="Directory with generated code."),
    out_dir: Path = typer.Option(DEFAULT_REPORTS_DIR, "--out", "-o", help="Output directory for test results."),
) -> None:
    """Run differential tests between golden model and generated code.

    TODO: Implement differential testing.
    """
    selected_spec = spec
    if selected_spec is None:
        candidates = sorted(DEFAULT_IR_DIR.glob("*.ir.yaml"))
        if not candidates:
            typer.echo(
                f"Error: no IR file found under default directory: {DEFAULT_IR_DIR}",
                err=True,
            )
            raise typer.Exit(code=1)
        selected_spec = candidates[0]

    if not selected_spec.exists():
        typer.echo(f"Error: Spec file does not exist: {selected_spec}", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"Running differential tests for: {selected_spec}")
    typer.echo(f"  gen: {gen_dir}")
    typer.echo(f"  out: {out_dir}")
    # TODO: call test runner
    typer.echo("TODO: differential testing not implemented")
    raise typer.Exit(code=0)
