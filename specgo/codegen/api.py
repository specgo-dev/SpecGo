# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""API wrapper codegen stub."""

from __future__ import annotations

from specgo.api_spec.model import ApiSpec
from specgo.ir.model import SpecIR


def generate_api(spec: SpecIR, api_spec: ApiSpec, out_dir: str) -> None:
    """Generate high-level API wrappers from ApiSpec and SpecIR.

    TODO: Implement mapping from API spec to protocol messages.
    """
    raise NotImplementedError("API codegen not implemented")
