# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""Codegen gates for generated C/H outputs."""

from __future__ import annotations

import hashlib
import subprocess
import tempfile
from pathlib import Path

from specgo.codegen.protocol import generate_protocol, protocol_output_filenames
from specgo.gates.evaluator import evaluate_codegen
from specgo.gates.metrics import CodegenGateMetrics, GateCheck
from specgo.ir.model import SpecIR


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _add_check(metrics: CodegenGateMetrics, name: str, passed: bool, detail: str = "") -> None:
    metrics.checks.append(GateCheck(name=name, passed=passed, detail=detail))


def _is_msvc(compiler: str) -> bool:
    """Check if the compiler is MSVC (cl.exe)."""
    return Path(compiler).stem.lower() == "cl"


def _run_compile_check(
    compiler: str,
    source_path: Path,
    include_dir: Path,
) -> tuple[bool, str]:
    if _is_msvc(compiler):
        # MSVC: /Zs = syntax check only
        cmd = [
            compiler,
            "/std:c11",
            "/W4",
            "/WX",
            f"/I{include_dir}",
            "/Zs",
            str(source_path),
        ]
    else:
        # GCC / Clang
        cmd = [
            compiler,
            "-std=c11",
            "-Wall",
            "-Wextra",
            "-Werror",
            f"-I{include_dir}",
            "-fsyntax-only",
            str(source_path),
        ]

    try:
        proc = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return False, f"compiler not found: {compiler}"

    if proc.returncode == 0:
        return True, "ok"

    stderr = (proc.stderr or "").strip()
    stdout = (proc.stdout or "").strip()
    detail = stderr if stderr else stdout
    return False, detail or f"compile failed with code {proc.returncode}"


def run_codegen_gates(
    spec: SpecIR,
    ir_path: Path,
    gen_dir: Path,
    *,
    lang: str = "c",
    compile_check: bool = True,
    compiler: str = "cc",
) -> CodegenGateMetrics:
    """Run gates against generated code files."""
    header_name, source_name = protocol_output_filenames(spec, lang=lang)
    expected = [header_name, source_name]
    expected_paths = [gen_dir / header_name, gen_dir / source_name]

    existing_files = [str(path) for path in expected_paths if path.exists()]
    total_size = sum(path.stat().st_size for path in expected_paths if path.exists())

    metrics = CodegenGateMetrics(
        ir_path=str(ir_path),
        gen_dir=str(gen_dir),
        expected_files=expected,
        existing_files=existing_files,
        total_size_bytes=total_size,
    )

    missing = [path.name for path in expected_paths if not path.exists()]
    _add_check(
        metrics,
        "files_exist",
        len(missing) == 0,
        "ok" if not missing else f"missing: {', '.join(missing)}",
    )

    if not missing:
        zero_sized = [path.name for path in expected_paths if path.stat().st_size == 0]
        _add_check(
            metrics,
            "files_non_empty",
            len(zero_sized) == 0,
            "ok" if not zero_sized else f"zero-sized: {', '.join(zero_sized)}",
        )

        include_line = f'#include "{header_name}"'
        source_text = (gen_dir / source_name).read_text(encoding="utf-8")
        _add_check(
            metrics,
            "source_includes_header",
            include_line in source_text,
            "ok" if include_line in source_text else f"missing include: {include_line}",
        )
    else:
        _add_check(metrics, "files_non_empty", False, "skipped: missing files")
        _add_check(metrics, "source_includes_header", False, "skipped: missing files")

    try:
        with tempfile.TemporaryDirectory(prefix="specgo-gate-ref-") as tmp_ref:
            ref_dir = Path(tmp_ref)
            ref_files = generate_protocol(spec, str(ref_dir), lang=lang)
            ref_map = {path.name: path for path in ref_files}

            output_match = True
            mismatch_reason = "ok"
            if not missing:
                for path in expected_paths:
                    if _file_sha256(path) != _file_sha256(ref_map[path.name]):
                        output_match = False
                        mismatch_reason = f"output mismatch: {path.name}"
                        break
            else:
                output_match = False
                mismatch_reason = "skipped: missing files"
            _add_check(metrics, "matches_current_templates", output_match, mismatch_reason)

        with tempfile.TemporaryDirectory(prefix="specgo-gate-det-a-") as tmp_a:
            with tempfile.TemporaryDirectory(prefix="specgo-gate-det-b-") as tmp_b:
                dir_a = Path(tmp_a)
                dir_b = Path(tmp_b)
                files_a = generate_protocol(spec, str(dir_a), lang=lang)
                files_b = generate_protocol(spec, str(dir_b), lang=lang)

                map_a = {path.name: _file_sha256(path) for path in files_a}
                map_b = {path.name: _file_sha256(path) for path in files_b}
                deterministic = map_a == map_b
                _add_check(
                    metrics,
                    "deterministic_codegen",
                    deterministic,
                    "ok" if deterministic else "hash mismatch across two generations",
                )
    except Exception as e:
        _add_check(metrics, "matches_current_templates", False, f"codegen error: {e}")
        _add_check(metrics, "deterministic_codegen", False, f"codegen error: {e}")

    if compile_check:
        source_path = gen_dir / source_name
        if source_path.exists():
            ok, detail = _run_compile_check(compiler, source_path, gen_dir)
            _add_check(metrics, "compile_syntax", ok, detail)
        else:
            _add_check(metrics, "compile_syntax", False, "skipped: source file missing")
    else:
        _add_check(metrics, "compile_syntax", True, "disabled")

    return metrics


def render_codegen_gate_report(metrics: CodegenGateMetrics) -> str:
    """Render a concise text report."""
    lines: list[str] = []
    overall = "PASSED" if evaluate_codegen(metrics) else "FAILED"
    lines.append(f"Codegen Gate: {overall}")
    lines.append(f"  IR: {metrics.ir_path}")
    lines.append(f"  Gen Dir: {metrics.gen_dir}")
    lines.append(f"  Expected: {', '.join(metrics.expected_files)}")
    lines.append(f"  Existing: {len(metrics.existing_files)}/{len(metrics.expected_files)}")
    lines.append(f"  Total Size: {metrics.total_size_bytes} bytes")
    lines.append("  Checks:")
    for check in metrics.checks:
        status = "PASS" if check.passed else "FAIL"
        detail = f" ({check.detail})" if check.detail else ""
        lines.append(f"    - [{status}] {check.name}{detail}")
    return "\n".join(lines)
