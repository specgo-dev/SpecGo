# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""API spec data model (minimal stub)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class ApiFunction:
    """A high-level API function mapping to one or more messages."""

    name: str
    description: str = ""
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)


@dataclass
class ApiSpec:
    """Root API spec object."""

    name: str
    version: str
    functions: List[ApiFunction] = field(default_factory=list)
