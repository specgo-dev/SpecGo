# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""Agent configuration.

TODO: Define configuration schema for the agent (model, budget, tool selection, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AgentConfig:
    """Configuration for the agent runner.

    TODO: Expand with real config fields.
    """

    max_iterations: int = 10
    model: str | None = None
