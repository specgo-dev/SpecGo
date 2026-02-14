# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""Gate evaluation helpers."""

from __future__ import annotations

from specgo.gates.metrics import CodegenGateMetrics, GateCheck, GateMetrics


def evaluate(metrics: GateMetrics) -> bool:
    """Evaluate metrics against thresholds.
    """
    if metrics.crash_count > 0:
        return False
    if metrics.hang_count > 0:
        return False
    if metrics.invariant_violations > 0:
        return False
    if metrics.conformance_error_rate > 0.0:
        return False
    return True


def evaluate_codegen(metrics: CodegenGateMetrics) -> bool:
    """Evaluate C/H codegen gate checks."""
    return all(check.passed for check in metrics.checks)


def failed_codegen_checks(metrics: CodegenGateMetrics) -> list[GateCheck]:
    """Get failed checks from codegen gate metrics."""
    return [check for check in metrics.checks if not check.passed]
