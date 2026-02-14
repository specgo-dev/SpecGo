# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""Agent budget management.

TODO: Track and enforce token/cost/iteration budgets.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Budget:
    """Token and iteration budget for an agent run.

    TODO: Implement budget tracking and enforcement.
    """

    max_tokens: int = 100_000
    max_iterations: int = 10
    tokens_used: int = 0
    iterations_used: int = 0

    @property
    def tokens_remaining(self) -> int:
        return self.max_tokens - self.tokens_used

    @property
    def iterations_remaining(self) -> int:
        return self.max_iterations - self.iterations_used

    @property
    def exhausted(self) -> bool:
        return self.tokens_remaining <= 0 or self.iterations_remaining <= 0
