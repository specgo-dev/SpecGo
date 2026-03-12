# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""Propose code patch — LLM action to fix failing tests in generated code.

TODO: Implement LLM-driven code patching when differential tests fail.
"""

from __future__ import annotations


def propose_code_patch(source_path: str, test_errors: list[str]) -> str:
    """Given generated code and test failures, propose a patched version.

    TODO: Implement LLM call with codegen prompt.
    """
    raise NotImplementedError("propose_code_patch not implemented")
