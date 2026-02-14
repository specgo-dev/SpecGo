# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""specgo start — bootstrap project workspace."""

from __future__ import annotations

import sys
from pathlib import Path

import typer

from specgo.cli.main import app
from specgo.workspace.bootstrap import (
    discover_project_root,
    ensure_global_config,
    ensure_project_workspace,
    save_global_config,
)


def _run_global_config_dialog(config: dict) -> dict:
    """Interactive first-time global config dialog."""
    typer.echo("")
    typer.echo("First-time SpecGo setup (global config)")
    typer.echo("Press Enter to keep defaults.")

    llm = config.get("llm")
    if not isinstance(llm, dict):
        llm = {}
        config["llm"] = llm
    budget = llm.get("budget")
    if not isinstance(budget, dict):
        budget = {}
        llm["budget"] = budget

    provider = typer.prompt("LLM provider", default=str(llm.get("provider", "") or ""))
    account = typer.prompt("LLM account", default=str(llm.get("account", "") or ""))
    token = typer.prompt("LLM token", default=str(llm.get("token", "") or ""), hide_input=True)

    max_tokens_raw = typer.prompt(
        "Budget max_tokens (empty for none)",
        default="" if budget.get("max_tokens") is None else str(budget.get("max_tokens")),
    ).strip()
    max_cost_raw = typer.prompt(
        "Budget max_cost_usd (empty for none)",
        default="" if budget.get("max_cost_usd") is None else str(budget.get("max_cost_usd")),
    ).strip()

    llm["provider"] = provider.strip()
    llm["account"] = account.strip()
    llm["token"] = token.strip()
    if max_tokens_raw:
        try:
            budget["max_tokens"] = int(max_tokens_raw)
        except ValueError as exc:
            raise ValueError("Budget max_tokens must be an integer or empty.") from exc
    else:
        budget["max_tokens"] = None

    if max_cost_raw:
        try:
            budget["max_cost_usd"] = float(max_cost_raw)
        except ValueError as exc:
            raise ValueError("Budget max_cost_usd must be a number or empty.") from exc
    else:
        budget["max_cost_usd"] = None
    return config


@app.command("start")
@app.command("init")
def cli_start(
    project: Path = typer.Option(
        Path("."),
        "--project",
        "-p",
        help="Project/repository path (auto-scans upward for .git).",
    ),
    no_dialog: bool = typer.Option(
        False,
        "--no-dialog",
        help="Skip first-time global configuration dialog.",
    ),
) -> None:
    """Bootstrap SpecGo workspace for a project."""
    project_input = project.expanduser()
    if not project_input.exists():
        typer.echo(f"Error: project path does not exist: {project_input}", err=True)
        raise typer.Exit(code=1)
    if project_input.is_file():
        project_input = project_input.parent
    if not project_input.is_dir():
        typer.echo(f"Error: project path is not a directory: {project_input}", err=True)
        raise typer.Exit(code=1)

    project_root = discover_project_root(project_input.resolve())

    try:
        global_cfg_path, global_cfg, global_created = ensure_global_config()
    except Exception as exc:
        typer.echo(f"Error: failed to initialize global config: {exc}", err=True)
        raise typer.Exit(code=1)

    if global_created and not no_dialog and sys.stdin.isatty():
        try:
            updated = _run_global_config_dialog(global_cfg)
        except ValueError as exc:
            typer.echo(f"Error: invalid global config input: {exc}", err=True)
            raise typer.Exit(code=1)
        try:
            save_global_config(updated)
        except Exception as exc:
            typer.echo(f"Error: failed to save global config: {exc}", err=True)
            raise typer.Exit(code=1)
        global_cfg = updated

    try:
        result = ensure_project_workspace(
            project_root=project_root,
            global_config=global_cfg,
        )
    except Exception as exc:
        typer.echo(f"Error: failed to bootstrap project workspace: {exc}", err=True)
        raise typer.Exit(code=1)

    typer.echo("Workspace bootstrap completed:")
    typer.echo(f"  project_root: {result.paths.project_root}")
    typer.echo(f"  workspace_dir: {result.paths.workspace_dir}")
    typer.echo(f"  global_config: {global_cfg_path}")
    typer.echo(f"  project_config: {result.paths.config_path}")
    typer.echo(f"  run_state: {result.paths.run_path}")
    typer.echo(f"  global_created: {global_created}")
    typer.echo(f"  workspace_created: {result.workspace_created}")
    typer.echo(f"  project_config_created: {result.project_config_created}")

    raise typer.Exit(code=0)
