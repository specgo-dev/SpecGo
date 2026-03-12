# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""specgo config — manage global/project config."""

from __future__ import annotations

from pathlib import Path

import typer
import yaml

from specgo.cli.main import app
from specgo.workspace.bootstrap import (
    discover_project_root,
    ensure_global_config,
    load_config,
    parse_scalar,
    resolve_workspace_dir_name,
    resolve_workspace_paths,
    save_config,
    save_global_config,
    set_dotted_value,
)

LOCKED_CONFIG_KEYS = {"workspace.dir_name", "workspace_dir_name"}


def _parse_assignments(assignments: list[str]) -> list[tuple[str, object]]:
    parsed: list[tuple[str, object]] = []
    for item in assignments:
        if "=" not in item:
            raise ValueError(f"Invalid --set '{item}', expected key=value")
        key, raw = item.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"Invalid --set '{item}', key is empty")
        parsed.append((key, parse_scalar(raw.strip())))
    return parsed


@app.command("config")
@app.command("cfg")
def cli_config(
    ctx: typer.Context,
    project: Path | None = typer.Option(
        None,
        "--project",
        "-p",
        help="Project/repository path (project-scope mode).",
    ),
    global_scope: bool = typer.Option(
        False,
        "--global",
        "-g",
        help="Use global config scope.",
    ),
    init: bool = typer.Option(
        False,
        "--init",
        help="Initialize config file if missing.",
    ),
    set_values: list[str] = typer.Option(
        [],
        "--set",
        help="Set config values via key=value (supports dotted keys). Repeatable.",
    ),
) -> None:
    """Show or update config files.

    Supports both:
    - `specgo config ...` (project scope)
    - `specgo -g config ...` or `specgo config -g ...` (global scope)
    """
    callback_global = False
    if isinstance(ctx.obj, dict):
        callback_global = bool(ctx.obj.get("global_scope"))
    use_global = callback_global or global_scope

    try:
        assignments = _parse_assignments(set_values)
    except ValueError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)
    for key, _ in assignments:
        if key in LOCKED_CONFIG_KEYS:
            typer.echo(
                f"Error: '{key}' is locked. Workspace directory name is fixed to '.specgo'.",
                err=True,
            )
            raise typer.Exit(code=1)

    if use_global:
        try:
            cfg_path, cfg, _ = ensure_global_config()
            for key, value in assignments:
                set_dotted_value(cfg, key, value)
            if assignments or init:
                cfg_path = save_global_config(cfg)
        except Exception as exc:
            typer.echo(f"Error: failed to process global config: {exc}", err=True)
            raise typer.Exit(code=1)

        typer.echo(f"Scope: global")
        typer.echo(f"Path: {cfg_path}")
        typer.echo(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True))
        raise typer.Exit(code=0)

    project_root = discover_project_root((project or Path.cwd()).resolve())
    _, global_cfg, _ = ensure_global_config()
    ws_name = resolve_workspace_dir_name(global_cfg)
    paths = resolve_workspace_paths(project_root, ws_name)

    if not paths.config_path.exists():
        if init:
            from specgo.workspace.bootstrap import ensure_project_workspace

            try:
                ensure_project_workspace(
                    project_root=project_root,
                    global_config=global_cfg,
                )
            except Exception as exc:
                typer.echo(f"Error: failed to initialize project config: {exc}", err=True)
                raise typer.Exit(code=1)
        else:
            typer.echo(
                f"Error: Project config does not exist: {paths.config_path}\n"
                f"Run 'specgo start' or use 'specgo config --init'.",
                err=True,
            )
            raise typer.Exit(code=1)

    try:
        cfg = load_config(paths.config_path)
        for key, value in assignments:
            set_dotted_value(cfg, key, value)
        if assignments:
            save_config(paths.config_path, cfg)
    except Exception as exc:
        typer.echo(f"Error: failed to process project config: {exc}", err=True)
        raise typer.Exit(code=1)

    typer.echo("Scope: project")
    typer.echo(f"Project Root: {project_root}")
    typer.echo(f"Workspace Dir: {paths.workspace_dir}")
    typer.echo(f"Path: {paths.config_path}")
    typer.echo(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True))
    raise typer.Exit(code=0)
