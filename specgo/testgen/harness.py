# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""Test harness generation stub."""

from __future__ import annotations

from specgo.api_spec.model import ApiSpec
from specgo.ir.model import SpecIR


def generate_tests(spec: SpecIR, api_spec: ApiSpec | None = None) -> None:
    """Generate tests and golden model.

    TODO: Implement differential and regression test generators.
    """
    raise NotImplementedError("Test generation not implemented")
