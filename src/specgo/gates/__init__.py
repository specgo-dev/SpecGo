# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""Quality gates and metrics."""

from specgo.gates.codegen import render_codegen_gate_report, run_codegen_gates
from specgo.gates.evaluator import evaluate, evaluate_codegen, failed_codegen_checks
from specgo.gates.io import load_validated_ir, validate_existing_codegen_dir
from specgo.gates.metrics import CodegenGateMetrics, GateCheck, GateMetrics

__all__ = [
    "GateMetrics",
    "GateCheck",
    "CodegenGateMetrics",
    "evaluate",
    "evaluate_codegen",
    "failed_codegen_checks",
    "load_validated_ir",
    "validate_existing_codegen_dir",
    "run_codegen_gates",
    "render_codegen_gate_report",
]
