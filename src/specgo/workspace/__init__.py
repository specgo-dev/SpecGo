# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""Workspace management for SpecGo.

Handles project layout conventions and artifact storage.
"""

from specgo.workspace.layout import WorkspaceLayout
from specgo.workspace.store import ArtifactStore
from specgo.workspace.bootstrap import (
    WorkspaceBootstrapResult,
    WorkspacePaths,
    discover_project_root,
    ensure_global_config,
    ensure_project_workspace,
    global_config_path,
    global_home_dir,
    resolve_workspace_paths,
)
from specgo.workspace.config_model import (
    CONFIG_APP_NAME,
    CONFIG_SCHEMA_VERSION,
    DEFAULT_WORKSPACE_DIR_NAME,
    GlobalConfig,
    ProjectConfig,
    RunState,
)

__all__ = [
    "WorkspaceLayout",
    "ArtifactStore",
    "CONFIG_SCHEMA_VERSION",
    "CONFIG_APP_NAME",
    "DEFAULT_WORKSPACE_DIR_NAME",
    "GlobalConfig",
    "ProjectConfig",
    "RunState",
    "WorkspacePaths",
    "WorkspaceBootstrapResult",
    "discover_project_root",
    "ensure_global_config",
    "ensure_project_workspace",
    "global_home_dir",
    "global_config_path",
    "resolve_workspace_paths",
]
