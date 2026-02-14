# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""Replay bundle model stub."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class ReplayEvent:
    """Single replay event in a timeline."""

    t_ms: int
    event: str
    message: str
    payload_hex: str


@dataclass
class ReplayBundle:
    """Replay bundle for deterministic execution."""

    spec_version: str
    seed: int
    timeline: List[ReplayEvent] = field(default_factory=list)
