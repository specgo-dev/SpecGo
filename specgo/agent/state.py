# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""Agent state tracking.

TODO: Track pipeline state across steps (current step, artifacts, errors).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentState:
    """Mutable state for a single agent run.

    TODO: Expand with real state fields.
    """

    current_step: str = ""
    artifacts: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
