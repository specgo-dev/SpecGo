# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""Layer 0: Schema validation via Pydantic.

Validates that the IR YAML conforms to the SpecIR model schema.
This is handled automatically by Pydantic's model_validate.
"""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from specgo.ir.model import SpecIR


def validate_schema(data: dict[str, Any]) -> tuple[SpecIR | None, list[str]]:
    """Validate raw IR data against the SpecIR Pydantic schema.

    Returns (SpecIR instance, []) on success, or (None, [error messages]) on failure.
    """
    errors: list[str] = []
    try:
        spec_ir = SpecIR.model_validate(data)
        return spec_ir, errors
    except ValidationError as e:
        for err in e.errors():
            loc = " -> ".join(str(l) for l in err["loc"])
            errors.append(f"[schema] {loc}: {err['msg']}")
        return None, errors
