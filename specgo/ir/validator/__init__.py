# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""IR validator package.

Layer 0: Schema validation (Pydantic model_validate)
Layer 1: Semantic validation (cross-field constraints)
"""

from __future__ import annotations

from typing import Any

from specgo.ir.model import SpecIR
from specgo.ir.validator.layer0_schema import validate_schema
from specgo.ir.validator.layer1_semantic import validate_semantic


def validate_ir(data: dict[str, Any]) -> tuple[SpecIR | None, list[str]]:
    """Run all validation layers on raw IR data.

    Returns (SpecIR instance, []) if valid,
    or (None, [error messages]) if Layer 0 fails,
    or (SpecIR instance, [error messages]) if Layer 1 fails.
    """
    # Layer 0: schema
    spec_ir, schema_errors = validate_schema(data)
    if schema_errors:
        return None, schema_errors

    # Layer 1: semantic
    semantic_errors = validate_semantic(spec_ir)
    return spec_ir, semantic_errors


__all__ = ["validate_ir", "validate_schema", "validate_semantic"]
