# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""CLI package for SpecGo."""

from specgo.cli.main import app

# Import command modules to register them with the app
from specgo.cli.commands import (
    cli_config,
    cli_protocol_codegen,
    cli_gate_codegen,
    cli_run,
    cli_spec_ingest,
    cli_spec_validate,
    cli_start,
    cli_test_diff,
    cli_test_roundtrip,
)

__all__ = ["app"]
