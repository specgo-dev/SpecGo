# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""Shared default paths for CLI commands."""

from __future__ import annotations

from pathlib import Path


DEFAULT_OUTPUT_ROOT = Path("specgo_output")
DEFAULT_IR_DIR = DEFAULT_OUTPUT_ROOT / "output"
DEFAULT_GEN_DIR = DEFAULT_OUTPUT_ROOT / "gen"
DEFAULT_REPORTS_DIR = DEFAULT_OUTPUT_ROOT / "reports"
DEFAULT_RAW_REPORTS_DIR = DEFAULT_OUTPUT_ROOT / "raw_reports"
DEFAULT_IR_GLOB = str(DEFAULT_IR_DIR / "*.ir.yaml")
