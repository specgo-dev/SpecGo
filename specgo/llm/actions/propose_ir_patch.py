# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""Propose IR patch — LLM action to fix validation errors in IR.

TODO: Implement LLM-driven IR patching using the ir_fix prompt template.
"""

from __future__ import annotations

from pathlib import Path


def propose_ir_patch(ir_path: Path, errors: list[str]) -> dict:
    """Given an IR file and validation errors, propose a patched IR.

    TODO: Implement LLM call with ir_fix prompt.
    """
    raise NotImplementedError("propose_ir_patch not implemented")
