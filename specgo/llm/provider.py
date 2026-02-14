# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""LLM provider — abstraction layer for LLM API calls.

TODO: Implement provider that supports multiple backends (OpenAI, Anthropic, etc.)
with unified interface, token counting, and budget enforcement.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LLMProvider:
    """Abstraction for LLM API access.

    TODO: Implement actual API calls, token counting, retries.
    """

    model: str = ""
    api_key: str | None = None
    base_url: str | None = None

    def complete(self, prompt: str) -> str:
        """Send a prompt and return the completion.

        TODO: Implement.
        """
        raise NotImplementedError("LLM provider not implemented")

    def count_tokens(self, text: str) -> int:
        """Count tokens in a text string.

        TODO: Implement.
        """
        raise NotImplementedError("Token counting not implemented")
