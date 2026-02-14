# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""specgo test-roundtrip — run seeded roundtrip property tests."""

from __future__ import annotations

import sys
from pathlib import Path

import typer

from specgo.cli.default_paths import DEFAULT_GEN_DIR, DEFAULT_IR_GLOB
from specgo.cli.main import app


@app.command("test-roundtrip")
@app.command("rt")
def cli_test_roundtrip(
    test_file_name: str = typer.Option(
        "roundtrip_property.py",
        "--test-file-name",
        "--test",
        help="Logical test file name stored in report metadata.",
    ),
    ir_glob: str = typer.Option(
        DEFAULT_IR_GLOB,
        "--ir-glob",
        "--ir",
        "-i",
        help="Glob pattern of IR YAML files used by the property tests.",
    ),
    artifact_dir: Path | None = typer.Option(
        DEFAULT_GEN_DIR,
        "--artifact-dir",
        "-a",
        help="Directory containing already-generated protocol C/H artifacts to test directly.",
    ),
    loops: int = typer.Option(
        10,
        "--loops",
        "-n",
        min=1,
        help="Number of loop iterations to execute.",
    ),
    master_seed: int | None = typer.Option(
        None,
        "--master-seed",
        "-m",
        help="Master seed for reproducible loop seed generation. If omitted, generated randomly and recorded.",
    ),
    seeds: str | None = typer.Option(
        None,
        "--seeds",
        "-s",
        help="Optional comma-separated seed list. Used first, then remaining loops are generated from master seed.",
    ),
    cases_per_seed: int = typer.Option(
        2,
        "--cases-per-seed",
        "-c",
        min=1,
        help="Number of random cases per seed per message.",
    ),
    compiler: str = typer.Option(
        "cl" if sys.platform == "win32" else "cc",
        "--compiler",
        help="Compiler used by property tests to build generated C source.",
    ),
    report_dir: Path | None = typer.Option(
        None,
        "--report-dir",
        "-r",
        help="Optional report output directory. Default is sibling directory `raw_reports` next to artifact dir/gen.",
    ),
    continue_on_fail: bool = typer.Option(
        True,
        "--continue-on-fail/--stop-on-fail",
        help="Continue remaining loops after failures.",
    ),
) -> None:
    """Run seeded raw roundtrip campaign and emit reproducible reports."""
    from specgo.testgen.raw.runner import run_raw_roundtrip_campaign

    typer.echo("Running raw roundtrip campaign:")
    typer.echo(f"  test_file_name: {test_file_name}")
    typer.echo(f"  ir_glob: {ir_glob}")
    typer.echo(f"  artifact_dir: {artifact_dir if artifact_dir is not None else '(auto-generate in temp dir)'}")
    typer.echo(f"  loops: {loops}")
    typer.echo(f"  master_seed: {master_seed if master_seed is not None else '(auto)'}")
    typer.echo(f"  seeds: {seeds if seeds is not None else '(none)'}")
    typer.echo(f"  cases_per_seed: {cases_per_seed}")
    typer.echo(f"  compiler: {compiler}")
    typer.echo(f"  report_dir: {report_dir if report_dir is not None else '(default raw_reports)'}")
    typer.echo(f"  continue_on_fail: {continue_on_fail}")

    try:
        summary_path, error_path, summary = run_raw_roundtrip_campaign(
            ir_glob=ir_glob,
            artifact_dir=artifact_dir,
            compiler=compiler,
            loops=loops,
            master_seed=master_seed,
            seed_list_raw=seeds,
            cases_per_seed=cases_per_seed,
            report_dir=report_dir,
            test_file_name=test_file_name,
            continue_on_fail=continue_on_fail,
        )
    except ValueError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)

    run_info = summary["raw_roundtrip_run"]
    run_summary = run_info["summary"]

    typer.echo("")
    typer.echo("Raw roundtrip summary:")
    typer.echo(f"  status: {run_summary['status']}")
    typer.echo(f"  loops_executed: {run_summary['total_loops_executed']}")
    typer.echo(f"  total_cases_run: {run_summary['total_cases_run']}")
    typer.echo(f"  total_failures: {run_summary['total_failures']}")
    typer.echo(f"  master_seed: {run_info['config']['master_seed']}")
    typer.echo(f"  loop_seeds: {run_info['config']['loop_seeds']}")
    typer.echo(f"  summary_report: {summary_path}")
    if error_path is not None:
        typer.echo(f"  error_report: {error_path}")

    if run_summary["status"] != "PASSED":
        raise typer.Exit(code=1)
    
    raise typer.Exit(code=0)
