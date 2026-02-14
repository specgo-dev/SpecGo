# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""CLI command modules.

Each module registers its commands with the main Typer app.
"""

from specgo.cli.commands.run import cli_run
from specgo.cli.commands.spec_ingest import cli_spec_ingest
from specgo.cli.commands.spec_validate import spec_validate as cli_spec_validate
from specgo.cli.commands.test_diff import cli_test_diff
from specgo.cli.commands.test_roundtrip import cli_test_roundtrip
from specgo.cli.commands.codegen_protocol import cli_protocol_codegen
from specgo.cli.commands.gate_codegen import cli_gate_codegen
from specgo.cli.commands.start import cli_start
from specgo.cli.commands.config import cli_config

__all__ = [
    "cli_run",
    "cli_spec_ingest",
    "cli_spec_validate",
    "cli_test_diff",
    "cli_test_roundtrip",
    "cli_protocol_codegen",
    "cli_gate_codegen",
    "cli_start",
    "cli_config",
]
