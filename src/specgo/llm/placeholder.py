# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""LLM assist placeholder.

TODO: Implement guarded LLM workflows with validation and budgets.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LlmAssist:
    """Placeholder configuration for LLM-assisted extraction."""

    enabled: bool = False
    model: str | None = None
    max_tokens: int | None = None
