# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""Internal IR models, validation, and IO utilities."""

from specgo.ir.model import Message, Signal, SpecIR
from specgo.ir.io import (
    validate_input_paths,
    validate_output_path,
    validate_output_dir,
    resolve_output_file,
    dump_yaml,
    dump_ir,
    load_yaml,
    load_ir,
)
from specgo.ir.validator import validate_ir

__all__ = [
    "SpecIR", "Message", "Signal",
    "validate_input_paths", "validate_output_path", "validate_output_dir",
    "resolve_output_file", "dump_yaml", "dump_ir", "load_yaml", "load_ir",
    "validate_ir",
]
