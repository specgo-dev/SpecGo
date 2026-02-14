# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""IO adapters for gate commands.

This module reuses IR-level IO/validation utilities so gate commands stay
consistent with the core ingest/validate workflow.
"""

from __future__ import annotations

from pathlib import Path

from specgo.ir.io import load_yaml, validate_input_paths
from specgo.ir.model import SpecIR
from specgo.ir.validator import validate_ir


def load_validated_ir(ir_path: Path) -> SpecIR:
    """Load an IR file and run both schema + semantic validation."""
    validate_input_paths([ir_path])
    raw = load_yaml(ir_path)
    spec_ir, errors = validate_ir(raw)
    if errors:
        raise ValueError("IR validation failed:\n" + "\n".join(f"- {err}" for err in errors))
    if spec_ir is None:
        raise ValueError("IR validation failed with no SpecIR result.")
    return spec_ir


def validate_existing_codegen_dir(gen_dir: Path) -> None:
    """Validate that codegen output directory exists and is a directory."""
    if not gen_dir.exists():
        raise FileNotFoundError(f"Generated directory does not exist: {gen_dir}")
    if not gen_dir.is_dir():
        raise ValueError(f"Expected generated directory, got file: {gen_dir}")
