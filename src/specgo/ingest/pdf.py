# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""PDF importer placeholder.

TODO: Extract text and structure from PDF specs.
"""

from __future__ import annotations

from pathlib import Path

from specgo.ir.model import SpecIR


def parse_pdf(path: Path) -> SpecIR:
    """Parse a PDF spec into SpecIR.

    TODO: Implement PDF parsing and LLM-assisted extraction.
    """
    raise NotImplementedError("PDF parsing not implemented")


def pdf_to_ir(path: Path) -> dict:
    """Convert a PDF file to an IR dict placeholder.

    TODO: Replace with real PDF -> SpecIR conversion.
    """
    return {"source": str(path), "format": "pdf", "ir": None}
