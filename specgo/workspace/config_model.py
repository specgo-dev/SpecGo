# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""Workspace config models and schema helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


CONFIG_SCHEMA_VERSION = "0.1"
CONFIG_APP_NAME = "specgo"
DEFAULT_WORKSPACE_DIR_NAME = ".specgo"


def utc_now_iso() -> str:
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


class WorkspaceConfig(BaseModel):
    """Global workspace-level settings."""

    model_config = ConfigDict(extra="allow")

    dir_name: str = DEFAULT_WORKSPACE_DIR_NAME


class BudgetConfig(BaseModel):
    """LLM budget settings."""

    model_config = ConfigDict(extra="allow")

    max_tokens: int | None = None
    max_cost_usd: float | None = None


class LLMConfig(BaseModel):
    """LLM provider/account settings."""

    model_config = ConfigDict(extra="allow")

    provider: str = ""
    account: str = ""
    token: str = ""
    budget: BudgetConfig = Field(default_factory=BudgetConfig)


class AgentConfig(BaseModel):
    """Agent runtime toggle/settings placeholder."""

    model_config = ConfigDict(extra="allow")

    enabled: bool = False


class GlobalConfig(BaseModel):
    """Global config file model (`~/.specgo/config`)."""

    model_config = ConfigDict(extra="allow")

    schema_version: str = CONFIG_SCHEMA_VERSION
    app: str = CONFIG_APP_NAME
    created_at_utc: str = Field(default_factory=utc_now_iso)
    updated_at_utc: str = Field(default_factory=utc_now_iso)
    workspace: WorkspaceConfig = Field(default_factory=WorkspaceConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)


class ProjectConfig(BaseModel):
    """Project config file model (`<project>/.specgo/config`)."""

    model_config = ConfigDict(extra="allow")

    schema_version: str = CONFIG_SCHEMA_VERSION
    app: str = CONFIG_APP_NAME
    project_name: str
    project_root: str
    workspace_dir_name: str = DEFAULT_WORKSPACE_DIR_NAME
    created_at_utc: str = Field(default_factory=utc_now_iso)
    updated_at_utc: str = Field(default_factory=utc_now_iso)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)


class RunState(BaseModel):
    """Run metadata model (`<project>/.specgo/run`)."""

    model_config = ConfigDict(extra="allow")

    schema_version: str = CONFIG_SCHEMA_VERSION
    timestamp_utc: str = Field(default_factory=utc_now_iso)
    specgo_version: str
    python_version: str
    platform: str
    project_root: str
    workspace_dir: str
    run_count: int = 1


def migrate_global_mapping(data: dict[str, Any]) -> dict[str, Any]:
    """Apply minimal migration defaults for global config mapping."""
    migrated = dict(data)
    migrated.setdefault("schema_version", CONFIG_SCHEMA_VERSION)
    migrated.setdefault("app", CONFIG_APP_NAME)
    return migrated


def migrate_project_mapping(data: dict[str, Any]) -> dict[str, Any]:
    """Apply minimal migration defaults for project config mapping."""
    migrated = dict(data)
    migrated.setdefault("schema_version", CONFIG_SCHEMA_VERSION)
    migrated.setdefault("app", CONFIG_APP_NAME)
    return migrated


def migrate_run_mapping(data: dict[str, Any]) -> dict[str, Any]:
    """Apply minimal migration defaults for run-state mapping."""
    migrated = dict(data)
    migrated.setdefault("schema_version", CONFIG_SCHEMA_VERSION)
    return migrated
