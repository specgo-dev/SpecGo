# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""LLM integration — provider, prompts, and actions.

Provides LLM API abstraction and structured actions for the agent pipeline.
"""

from specgo.llm.placeholder import LlmAssist
from specgo.llm.provider import LLMProvider

__all__ = ["LlmAssist", "LLMProvider"]
