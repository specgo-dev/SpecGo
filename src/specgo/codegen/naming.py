# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""Central naming policy for protocol C codegen artifacts and symbols."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProtocolMessageSymbols:
    """Resolved C symbols for one protocol message."""

    project_c_name: str
    message_c_name: str
    struct_name: str
    encode_fn: str
    decode_fn: str
    id_macro: str
    dlc_macro: str


def c_identifier(name: str) -> str:
    """Normalize arbitrary text into a C-safe identifier."""
    cleaned = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in name)
    cleaned = cleaned.strip("_") or "unnamed"
    if cleaned[0].isdigit():
        cleaned = f"_{cleaned}"
    return cleaned


def protocol_header_guard(project_name: str) -> str:
    """Build header guard symbol for one project."""
    project_c_name = c_identifier(project_name)
    return f"SPECGO_{project_c_name.upper()}_PROTOCOL_H"


def protocol_output_filenames_for_project(project_name: str) -> tuple[str, str]:
    """Get protocol output filenames (header, source) for one project name."""
    project_c_name = c_identifier(project_name)
    return (f"{project_c_name}_protocol.h", f"{project_c_name}_protocol.c")


def protocol_message_symbols(project_name: str, message_name: str) -> ProtocolMessageSymbols:
    """Build stable symbol names for one project/message pair."""
    project_c_name = c_identifier(project_name)
    message_c_name = c_identifier(message_name)
    macro_prefix = f"SPECGO_{project_c_name.upper()}_{message_c_name.upper()}"
    return ProtocolMessageSymbols(
        project_c_name=project_c_name,
        message_c_name=message_c_name,
        struct_name=f"{project_c_name}_{message_c_name}_t",
        encode_fn=f"{project_c_name}_encode_{message_c_name}",
        decode_fn=f"{project_c_name}_decode_{message_c_name}",
        id_macro=f"{macro_prefix}_ID",
        dlc_macro=f"{macro_prefix}_DLC",
    )
