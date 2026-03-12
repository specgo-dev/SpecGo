# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""Workspace bootstrap and config helpers.

This module focuses on workspace/config entry plumbing only.
It intentionally avoids prescribing the full internal workspace layout.
"""

from __future__ import annotations

import platform
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from specgo import __version__
from specgo.workspace.config_model import (
    DEFAULT_WORKSPACE_DIR_NAME,
    GlobalConfig,
    LLMConfig,
    ProjectConfig,
    RunState,
    migrate_global_mapping,
    migrate_project_mapping,
    migrate_run_mapping,
    utc_now_iso,
)


GLOBAL_HOME_DIR_NAME = ".specgo"


@dataclass(frozen=True)
class WorkspacePaths:
    """Resolved workspace paths for one project."""

    project_root: Path
    workspace_dir: Path
    config_path: Path
    run_path: Path


@dataclass(frozen=True)
class WorkspaceBootstrapResult:
    """Result details after workspace bootstrap."""

    paths: WorkspacePaths
    workspace_created: bool
    project_config_created: bool
    run_initialized: bool


def _read_yaml_mapping(path: Path) -> dict[str, Any]:
    """Read a YAML mapping file.

    Returns empty dict when file does not exist.
    """
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected YAML mapping in {path}, got {type(data).__name__}")
    return data


def _write_yaml_mapping(path: Path, data: dict[str, Any]) -> None:
    """Write a YAML mapping with stable formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            data,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
        ),
        encoding="utf-8",
    )


def global_home_dir() -> Path:
    """Get global SpecGo home directory path."""
    return Path.home() / GLOBAL_HOME_DIR_NAME


def global_config_path() -> Path:
    """Get global config file path."""
    return global_home_dir() / "config"


def default_global_config() -> dict[str, Any]:
    """Build default global config."""
    return GlobalConfig().model_dump(mode="python")


def _validate_global_config(config: dict[str, Any]) -> dict[str, Any]:
    model = GlobalConfig.model_validate(migrate_global_mapping(config))
    # Workspace directory name is fixed to prevent project workspace relocation surprises.
    model.workspace.dir_name = DEFAULT_WORKSPACE_DIR_NAME
    return model.model_dump(mode="python")


def _validate_project_config(config: dict[str, Any]) -> dict[str, Any]:
    model = ProjectConfig.model_validate(migrate_project_mapping(config))
    return model.model_dump(mode="python")


def _validate_run_state(config: dict[str, Any]) -> dict[str, Any]:
    model = RunState.model_validate(migrate_run_mapping(config))
    return model.model_dump(mode="python")


def ensure_global_config() -> tuple[Path, dict[str, Any], bool]:
    """Ensure global config exists.

    Returns:
    - config path
    - config mapping
    - whether it was newly created
    """
    path = global_config_path()
    created = False
    if not path.exists():
        cfg = default_global_config()
        _write_yaml_mapping(path, cfg)
        created = True
    else:
        cfg = _validate_global_config(_read_yaml_mapping(path))
        _write_yaml_mapping(path, cfg)
    return path, cfg, created


def save_global_config(config: dict[str, Any]) -> Path:
    """Persist global config and return its path."""
    path = global_config_path()
    validated = _validate_global_config(config)
    validated["updated_at_utc"] = utc_now_iso()
    _write_yaml_mapping(path, validated)
    return path


def discover_project_root(start: Path) -> Path:
    """Discover project root by scanning upward for .git.

    Falls back to the provided directory when no .git is found.
    """
    current = start.resolve()
    if current.is_file():
        current = current.parent

    for candidate in [current, *current.parents]:
        if (candidate / ".git").exists():
            return candidate
    return current


def resolve_workspace_dir_name(
    global_config: dict[str, Any],
) -> str:
    """Resolve workspace directory name."""
    _ = global_config
    return DEFAULT_WORKSPACE_DIR_NAME


def resolve_workspace_paths(project_root: Path, workspace_dir_name: str) -> WorkspacePaths:
    """Resolve workspace file paths."""
    chosen = project_root / workspace_dir_name

    return WorkspacePaths(
        project_root=project_root,
        workspace_dir=chosen,
        config_path=chosen / "config",
        run_path=chosen / "run",
    )


def default_project_config(
    *,
    project_root: Path,
    global_config: dict[str, Any],
) -> dict[str, Any]:
    """Build default per-project config."""
    global_model = GlobalConfig.model_validate(migrate_global_mapping(global_config))
    model = ProjectConfig(
        project_name=project_root.name,
        project_root=str(project_root),
        workspace_dir_name=DEFAULT_WORKSPACE_DIR_NAME,
        llm=LLMConfig.model_validate(global_model.llm.model_dump(mode="python")),
    )
    return model.model_dump(mode="python")


def ensure_project_workspace(
    *,
    project_root: Path,
    global_config: dict[str, Any],
) -> WorkspaceBootstrapResult:
    """Ensure project workspace dir and required bootstrap files exist.

    This creates:
    - `<workspace>/config` (project config)
    - `<workspace>/run` (last run/bootstrap metadata)
    """
    resolved_name = resolve_workspace_dir_name(global_config)
    paths = resolve_workspace_paths(project_root, resolved_name)

    workspace_created = False
    if not paths.workspace_dir.exists():
        paths.workspace_dir.mkdir(parents=True, exist_ok=True)
        workspace_created = True

    project_config_created = False
    if not paths.config_path.exists():
        project_cfg = default_project_config(
            project_root=project_root,
            global_config=global_config,
        )
        _write_yaml_mapping(paths.config_path, project_cfg)
        project_config_created = True
    else:
        project_cfg = _validate_project_config(_read_yaml_mapping(paths.config_path))
        _write_yaml_mapping(paths.config_path, project_cfg)

    previous_run: dict[str, Any] = {}
    if paths.run_path.exists():
        try:
            previous_run = _validate_run_state(_read_yaml_mapping(paths.run_path))
        except Exception:
            previous_run = {}
    previous_count = previous_run.get("run_count", 0)
    run_count = previous_count + 1 if isinstance(previous_count, int) else 1
    run_data = RunState(
        timestamp_utc=utc_now_iso(),
        specgo_version=__version__,
        python_version=platform.python_version(),
        platform=platform.platform(),
        project_root=str(project_root),
        workspace_dir=str(paths.workspace_dir),
        run_count=run_count,
    ).model_dump(mode="python")
    _write_yaml_mapping(paths.run_path, run_data)

    return WorkspaceBootstrapResult(
        paths=paths,
        workspace_created=workspace_created,
        project_config_created=project_config_created,
        run_initialized=True,
    )


def load_config(path: Path) -> dict[str, Any]:
    """Load a config mapping file."""
    return _validate_project_config(_read_yaml_mapping(path))


def save_config(path: Path, config: dict[str, Any]) -> None:
    """Save a config mapping file."""
    validated = _validate_project_config(config)
    validated["updated_at_utc"] = utc_now_iso()
    _write_yaml_mapping(path, validated)


def set_dotted_value(config: dict[str, Any], dotted_key: str, value: Any) -> None:
    """Set nested key value using dotted notation."""
    parts = [part.strip() for part in dotted_key.split(".") if part.strip()]
    if not parts:
        raise ValueError("Empty config key is not allowed")

    cursor: dict[str, Any] = config
    for part in parts[:-1]:
        existing = cursor.get(part)
        if not isinstance(existing, dict):
            existing = {}
            cursor[part] = existing
        cursor = existing
    cursor[parts[-1]] = value


def parse_scalar(raw: str) -> Any:
    """Parse a scalar value from CLI text."""
    lowered = raw.strip().lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"none", "null"}:
        return None

    try:
        if "." in raw:
            return float(raw)
        return int(raw)
    except ValueError:
        return raw
