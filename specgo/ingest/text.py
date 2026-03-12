# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""Plain-text importer placeholder.

TODO: Extract structure from text specs.
"""

from __future__ import annotations

from pathlib import Path

from specgo.ir.model import SpecIR


def parse_text(path: Path) -> SpecIR:
    """Parse a text spec into SpecIR.

    TODO: Implement text parsing and LLM-assisted extraction.
    """
    raise NotImplementedError("Text parsing not implemented")


def text_to_ir(path: Path) -> dict:
    """Convert a text file to an IR dict placeholder.

    TODO: Replace with real text -> SpecIR conversion.
    """
    return {"source": str(path), "format": "text", "ir": None}
