# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""Spec ingestion package.

Dispatches spec files (DBC, PDF, text) to format-specific converters.
"""

from specgo.ingest.dispatcher import spec_dispatch

__all__ = ["spec_dispatch"]