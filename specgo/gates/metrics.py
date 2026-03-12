# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""Gate metrics models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class GateMetrics:
    """Quality metrics captured from tests and replays."""

    crash_count: int = 0
    hang_count: int = 0
    invariant_violations: int = 0
    conformance_error_rate: float = 0.0
    latency_p95_ms: float | None = None


@dataclass
class GateCheck:
    """Single gate check result."""

    name: str
    passed: bool
    detail: str = ""


@dataclass
class CodegenGateMetrics:
    """Metrics and check results for generated code gates."""

    ir_path: str
    gen_dir: str
    expected_files: list[str]
    existing_files: list[str] = field(default_factory=list)
    total_size_bytes: int = 0
    checks: list[GateCheck] = field(default_factory=list)
