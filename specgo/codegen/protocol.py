# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""Protocol encoder/decoder codegen via Jinja2 templates."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from specgo.codegen.naming import (
    c_identifier,
    protocol_header_guard,
    protocol_message_symbols,
    protocol_output_filenames_for_project,
)
from specgo.codegen.render import render_to_file
from specgo.ir.model import SpecIR


def _unsigned_max(bit_length: int) -> int:
    """Maximum unsigned value for the given bit length."""
    if bit_length >= 64:
        return (1 << 64) - 1
    return (1 << bit_length) - 1


def _signed_min(bit_length: int) -> int:
    """Minimum signed value for the given bit length."""
    if bit_length >= 64:
        return -(1 << 63)
    return -(1 << (bit_length - 1))


def _signed_max(bit_length: int) -> int:
    """Maximum signed value for the given bit length."""
    if bit_length >= 64:
        return (1 << 63) - 1
    return (1 << (bit_length - 1)) - 1


def _u64_mask_literal(bit_length: int) -> str:
    """Build a uint64_t mask literal for a bit length."""
    if bit_length >= 64:
        return "UINT64_MAX"
    return f"0x{((1 << bit_length) - 1):X}ULL"


def _bit_positions_lsb_first(start_bit: int, bit_length: int, byte_order: str) -> list[int]:
    """Build absolute payload bit positions ordered from LSB to MSB."""
    if byte_order == "little_endian":
        return list(range(start_bit, start_bit + bit_length))

    if byte_order == "big_endian":
        # DBC Motorola layout: start_bit is signal MSB.
        msb_to_lsb: list[int] = []
        bit_pos = start_bit
        for _ in range(bit_length):
            msb_to_lsb.append(bit_pos)
            if bit_pos % 8 == 0:
                bit_pos += 15
            else:
                bit_pos -= 1
        return list(reversed(msb_to_lsb))

    raise ValueError(f"Unsupported byte_order '{byte_order}'")


def _build_context(spec: SpecIR) -> dict[str, Any]:
    """Convert SpecIR into template-ready protocol context."""
    project_c_name = c_identifier(spec.meta.name)
    messages = []
    has_signed_signals = False

    for msg in sorted(spec.messages, key=lambda item: (item.id, item.name)):
        symbols = protocol_message_symbols(spec.meta.name, msg.name)
        signals = []
        for sig in sorted(msg.signals, key=lambda item: (item.start_bit, item.name)):
            if sig.bit_length > 64:
                raise ValueError(
                    f"Unsupported bit_length {sig.bit_length} in message "
                    f"'{msg.name}', signal '{sig.name}'. Max supported is 64."
                )
            bit_positions = _bit_positions_lsb_first(
                sig.start_bit,
                sig.bit_length,
                sig.byte_order,
            )

            sig_c_name = c_identifier(sig.name)
            if sig.signed:
                has_signed_signals = True
                c_type = "int64_t"
                range_min = _signed_min(sig.bit_length)
                range_max = _signed_max(sig.bit_length)
                range_min_c = "INT64_MIN" if sig.bit_length >= 64 else f"{range_min}LL"
                range_max_c = "INT64_MAX" if sig.bit_length >= 64 else f"{range_max}LL"
            else:
                c_type = "uint64_t"
                range_min = 0
                range_max = _unsigned_max(sig.bit_length)
                range_min_c = "0ULL"
                range_max_c = "UINT64_MAX" if sig.bit_length >= 64 else f"{range_max}ULL"

            signals.append(
                {
                    "name": sig.name,
                    "c_name": sig_c_name,
                    "c_type": c_type,
                    "start_bit": sig.start_bit,
                    "bit_length": sig.bit_length,
                    "signed": sig.signed,
                    "byte_order": sig.byte_order,
                    "scale": sig.scale,
                    "offset": sig.offset,
                    "range_min": range_min,
                    "range_max": range_max,
                    "range_min_c": range_min_c,
                    "range_max_c": range_max_c,
                    "bit_mask_c": _u64_mask_literal(sig.bit_length),
                    "bit_positions_c": ", ".join(f"{position}U" for position in bit_positions),
                }
            )

        messages.append(
            {
                "name": msg.name,
                "c_name": symbols.message_c_name,
                "struct_name": symbols.struct_name,
                "id": msg.id,
                "dlc": msg.dlc,
                "id_macro": symbols.id_macro,
                "dlc_macro": symbols.dlc_macro,
                "encode_fn": symbols.encode_fn,
                "decode_fn": symbols.decode_fn,
                "signals": signals,
            }
        )

    header_name, source_name = protocol_output_filenames_for_project(spec.meta.name)
    return {
        "project_name": spec.meta.name,
        "project_c_name": project_c_name,
        "header_guard": protocol_header_guard(spec.meta.name),
        "header_filename": header_name,
        "source_filename": source_name,
        "messages": messages,
        "has_signed_signals": has_signed_signals,
    }


def generate_protocol(spec: SpecIR, out_dir: str, lang: str = "c") -> list[Path]:
    """Generate protocol code from SpecIR.

    Emits protocol-level C code (header/source) via Jinja2 templates.
    """
    if lang != "c":
        raise ValueError(f"Unsupported language '{lang}'. Only 'c' is currently supported.")

    context = _build_context(spec)
    output_root = Path(out_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    header_path = output_root / context["header_filename"]
    source_path = output_root / context["source_filename"]

    render_to_file("c/protocol.h.j2", context, header_path)
    render_to_file("c/protocol.c.j2", context, source_path)

    return [header_path, source_path]


def protocol_output_filenames(spec: SpecIR, lang: str = "c") -> tuple[str, str]:
    """Get expected output file names for protocol codegen."""
    if lang != "c":
        raise ValueError(f"Unsupported language '{lang}'. Only 'c' is currently supported.")
    return protocol_output_filenames_for_project(spec.meta.name)
