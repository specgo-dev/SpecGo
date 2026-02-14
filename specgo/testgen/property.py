# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""Seeded property-test helpers for protocol roundtrip checks."""

from __future__ import annotations

import random

from specgo.codegen.naming import c_identifier
from specgo.ir.model import Message, Signal


def signal_bit_positions_lsb_first(sig: Signal) -> list[int]:
    """Build absolute payload bit positions ordered from LSB to MSB."""
    if sig.byte_order == "little_endian":
        return list(range(sig.start_bit, sig.start_bit + sig.bit_length))

    if sig.byte_order == "big_endian":
        msb_to_lsb: list[int] = []
        bit_pos = sig.start_bit
        for _ in range(sig.bit_length):
            msb_to_lsb.append(bit_pos)
            if bit_pos % 8 == 0:
                bit_pos += 15
            else:
                bit_pos -= 1
        return list(reversed(msb_to_lsb))

    raise ValueError(f"Unsupported byte_order '{sig.byte_order}' for signal '{sig.name}'")


def message_occupied_bits(msg: Message) -> set[int]:
    """Get union of occupied bit positions for all signals in a message."""
    occupied: set[int] = set()
    for sig in msg.signals:
        occupied.update(signal_bit_positions_lsb_first(sig))
    return occupied


def signal_raw_range(sig: Signal) -> tuple[int, int]:
    """Get valid raw integer range for a signal."""
    if sig.signed:
        if sig.bit_length >= 64:
            return (-(1 << 63), (1 << 63) - 1)
        return (-(1 << (sig.bit_length - 1)), (1 << (sig.bit_length - 1)) - 1)

    if sig.bit_length >= 64:
        return (0, (1 << 64) - 1)
    return (0, (1 << sig.bit_length) - 1)


def random_raw_value(sig: Signal, rng: random.Random) -> int:
    """Generate a seeded random raw value for a signal.

    Boundary values are sampled frequently to stress edge cases.
    """
    lo, hi = signal_raw_range(sig)
    candidates = {lo, hi, 0}
    if lo <= 1 <= hi:
        candidates.add(1)
    if lo <= -1 <= hi:
        candidates.add(-1)

    # 50% boundary values, 50% full-range random
    if rng.random() < 0.5:
        pick = sorted(candidates)
        return pick[rng.randrange(0, len(pick))]
    return rng.randint(lo, hi)
