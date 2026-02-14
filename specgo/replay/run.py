# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""Replay execution stub."""

from __future__ import annotations

from specgo.replay.model import ReplayBundle


def run_replay(bundle: ReplayBundle, out_dir: str) -> None:
    """Run a replay bundle and emit results.

    TODO: Implement deterministic replay and fault injection.
    """
    raise NotImplementedError("Replay run not implemented")
