# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""DBC importer — parse DBC files into Spec IR using cantools."""

from __future__ import annotations

from pathlib import Path

import cantools

from specgo.ir.model import (
    BusType, EnumEntry, IRMeta, Message, Signal, SpecIR,
)


def dbc_to_ir(path: Path) -> dict:
    """Convert a DBC file to an IR dict via SpecIR model."""
    if not path.exists():
        raise FileNotFoundError(f"DBC file not found: {path}")
    if not path.is_file():
        raise ValueError(f"DBC path is not a file: {path}")
    if path.suffix.lower() != ".dbc":
        raise ValueError(f"Input file is not a .dbc file: {path}")

    db = cantools.database.load_file(str(path))

    # DBC is always CAN; detect classic vs FD from message flags
    mode = "fd" if any(m.is_fd for m in db.messages) else "classic"
    bus_type = BusType(bustype="CAN", busmode=mode)

    # Build messages
    messages = []
    for msg in db.messages:
        signals = []
        for sig in msg.signals:
            raw_order = sig.byte_order
            if raw_order == "little_endian":
                byte_order = "little_endian"
            elif raw_order == "big_endian":
                byte_order = "big_endian"
            else:
                byte_order = "unknown"

            # Build enum entries if the signal has named values
            enum_entries = None
            if sig.choices:
                sorted_choices = sorted(sig.choices.items(), key=lambda item: item[0])  # Sort by value
                enum_entries = [
                    EnumEntry(name=str(name), value=val)
                    for val, name in sorted_choices
                ]

            signals.append(Signal(
                name=sig.name,
                start_bit=sig.start,
                bit_length=sig.length,
                byte_order=byte_order,
                signed=sig.is_signed,
                scale=sig.scale,
                offset=sig.offset,
                min=sig.minimum,
                default=sig.initial,
                max=sig.maximum,
                unit=sig.unit or None,
                enum=enum_entries,
            ))

        messages.append(Message(
            id=msg.frame_id,
            name=msg.name,
            dlc=msg.length,
            is_extended=msg.is_extended_frame,
            is_fd=msg.is_fd,
            description=msg.comment or None,
            signals=signals,
        ))

    meta = IRMeta(
        name=path.stem,
        version=db.version if db.version else "unknown",
        source=str(path),
        format="dbc",
    )

    spec_ir = SpecIR(
        meta=meta,
        bus_type=bus_type,
        messages=messages,
    )

    return spec_ir.model_dump()
