# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""IO Dispatcher for SpecGo.

This module dispatches spec files to the appropriate converter based on file suffix.
"""

from __future__ import annotations

from pathlib import Path

from specgo.ingest.dbc import dbc_to_ir
from specgo.ingest.pdf import pdf_to_ir
from specgo.ingest.text import text_to_ir

SUFFIX_DISPATCH: dict[str, callable] = {
    ".dbc": dbc_to_ir,
    ".pdf": pdf_to_ir,
    ".txt": text_to_ir,
    ".text": text_to_ir,
    ".md": text_to_ir,
}

SUPPORTED_SUFFIXES = sorted(SUFFIX_DISPATCH.keys())


def spec_dispatch(path: Path) -> dict:
    """Dispatch a spec file to the appropriate converter based on its suffix.

    Returns an IR dict placeholder from the matched converter.
    Raises ValueError for unsupported file types.
    """
    suffix = path.suffix.lower()
    converter = SUFFIX_DISPATCH.get(suffix)
    if converter is None:
        raise ValueError(
            f"Unsupported file type '{suffix}' for: {path}\n"
            f"Supported types: {', '.join(SUPPORTED_SUFFIXES)}"
        )
    return converter(path)
