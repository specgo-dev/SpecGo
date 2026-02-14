# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""Seeded raw roundtrip campaign runner."""

from __future__ import annotations

import ctypes
import glob
import random
import shutil
import subprocess
import sys
import tempfile
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from specgo import __version__
from specgo.codegen.naming import c_identifier, protocol_message_symbols
from specgo.codegen.protocol import generate_protocol, protocol_output_filenames
from specgo.ir.io import load_yaml
from specgo.ir.model import Message, SpecIR
from specgo.ir.validator import validate_ir
from specgo.testgen.property import message_occupied_bits, random_raw_value
from specgo.testgen.raw.io import resolve_report_dir, utc_now_iso, utc_timestamp_slug, write_raw_reports


@dataclass
class MessageBinding:
    """Bound ctypes handles for one message's protocol functions."""

    message: Message
    encode_name: str
    decode_name: str
    struct_type: type[ctypes.Structure]
    encode_fn: Any
    decode_fn: Any
    field_names: list[str]
    occupied_bits: set[int]


@dataclass
class SpecBinding:
    """Compiled binding for one IR spec/project."""

    spec: SpecIR
    ir_path: Path
    project_name: str
    ir_version: str
    source_path: Path
    header_path: Path
    library_path: Path
    messages: list[MessageBinding]


def _shared_library_suffix() -> str:
    if sys.platform == "darwin":
        return ".dylib"
    if sys.platform == "win32":
        return ".dll"
    return ".so"


def _parse_seed_list(raw: str | None) -> list[int]:
    if raw is None or raw.strip() == "":
        return []
    items = [item.strip() for item in raw.split(",")]
    return [int(item) for item in items if item]


def _resolve_master_seed(master_seed: int | None) -> int:
    if master_seed is not None:
        return int(master_seed)
    return random.SystemRandom().randrange(0, 2**63)


def _resolve_loop_seeds(*, loops: int, master_seed: int, explicit_seeds: list[int]) -> list[int]:
    rng = random.Random(master_seed)
    seeds: list[int] = []
    for idx in range(loops):
        if idx < len(explicit_seeds):
            seeds.append(explicit_seeds[idx])
        else:
            seeds.append(rng.randrange(0, 2**31))
    return seeds


def _is_msvc(compiler: str) -> bool:
    """Check if the compiler is MSVC (cl.exe)."""
    base = Path(compiler).stem.lower()
    return base == "cl"


def _compiler_version(compiler: str) -> str:
    flag = "" if _is_msvc(compiler) else "--version"
    cmd = [compiler, flag] if flag else [compiler]
    try:
        proc = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return f"{compiler}: not found"
    text = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
    first = text.splitlines()[0] if text else ""
    return first or f"{compiler}: version unknown"


def _iter_ir_files(ir_glob: str) -> list[Path]:
    paths = [Path(path).resolve() for path in glob.glob(ir_glob, recursive=True)]
    return sorted(path for path in paths if path.suffix == ".yaml" and path.name.endswith(".ir.yaml"))


def _sorted_signals(msg: Message):
    return sorted(msg.signals, key=lambda item: (item.start_bit, item.name))


def _compile_shared_library(
    *,
    source_path: Path,
    include_dir: Path,
    output_path: Path,
    compiler: str,
) -> None:
    if _is_msvc(compiler):
        cmd = [
            compiler,
            "/LD",
            "/std:c11",
            "/W4",
            "/WX",
            str(source_path),
            f"/I{include_dir}",
            f"/Fe:{output_path}",
        ]
        proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
        if proc.returncode == 0:
            return
        raise RuntimeError(
            f"Failed to compile generated source ({source_path.name}) with MSVC.\n"
            f"stderr: {proc.stderr}"
        )

    # GCC / Clang
    common = [
        "-std=c11",
        "-Wall",
        "-Wextra",
        "-Werror",
        str(source_path),
        f"-I{include_dir}",
        "-o",
        str(output_path),
    ]

    primary = [compiler, "-shared", "-fPIC", *common]
    proc = subprocess.run(primary, check=False, capture_output=True, text=True)
    if proc.returncode == 0:
        return

    if sys.platform == "darwin":
        fallback = [compiler, "-dynamiclib", *common]
        fallback_proc = subprocess.run(fallback, check=False, capture_output=True, text=True)
        if fallback_proc.returncode == 0:
            return
        raise RuntimeError(
            f"Failed to compile generated source ({source_path.name}).\n"
            f"primary stderr: {proc.stderr}\n"
            f"fallback stderr: {fallback_proc.stderr}"
        )

    raise RuntimeError(
        f"Failed to compile generated source ({source_path.name}).\n"
        f"stderr: {proc.stderr}"
    )


def _build_message_binding(lib: ctypes.CDLL, spec: SpecIR, msg: Message) -> MessageBinding:
    symbols = protocol_message_symbols(spec.meta.name, msg.name)
    struct_name = symbols.struct_name
    encode_name = symbols.encode_fn
    decode_name = symbols.decode_fn

    fields: list[tuple[str, type[ctypes._SimpleCData]]] = []
    for sig in _sorted_signals(msg):
        field_name = c_identifier(sig.name)
        field_type = ctypes.c_int64 if sig.signed else ctypes.c_uint64
        fields.append((field_name, field_type))

    struct_type = type(struct_name, (ctypes.Structure,), {"_fields_": fields})
    field_names = [name for name, _ in fields]

    encode_fn = getattr(lib, encode_name)
    encode_fn.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t,
        ctypes.POINTER(struct_type),
    ]
    encode_fn.restype = ctypes.c_int

    decode_fn = getattr(lib, decode_name)
    decode_fn.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t,
        ctypes.POINTER(struct_type),
    ]
    decode_fn.restype = ctypes.c_int

    return MessageBinding(
        message=msg,
        encode_name=encode_name,
        decode_name=decode_name,
        struct_type=struct_type,
        encode_fn=encode_fn,
        decode_fn=decode_fn,
        field_names=field_names,
        occupied_bits=message_occupied_bits(msg),
    )


def _bit(payload: ctypes.Array[ctypes.c_uint8], bit_index: int) -> int:
    byte_index = bit_index // 8
    bit_in_byte = bit_index % 8
    return (int(payload[byte_index]) >> bit_in_byte) & 0x1


def _random_struct(binding: MessageBinding, rng: random.Random) -> ctypes.Structure:
    obj = binding.struct_type()
    for sig in _sorted_signals(binding.message):
        setattr(obj, c_identifier(sig.name), random_raw_value(sig, rng))
    return obj


def _make_failure(
    *,
    loop_index: int,
    seed: int,
    project_name: str,
    ir_path: Path,
    ir_version: str | None,
    message_name: str,
    encode_fn: str,
    decode_fn: str,
    property_name: str,
    case_index: int | None,
    detail: str,
    exc: Exception | None = None,
) -> dict[str, Any]:
    failure: dict[str, Any] = {
        "timestamp_utc": utc_now_iso(),
        "loop_index": loop_index,
        "seed": seed,
        "project_name": project_name,
        "ir_path": str(ir_path),
        "ir_version": ir_version,
        "message_name": message_name,
        "encode_fn": encode_fn,
        "decode_fn": decode_fn,
        "property": property_name,
        "case_index": case_index,
        "detail": detail,
    }
    if exc is not None:
        failure["exception"] = str(exc)
        failure["traceback"] = traceback.format_exc()
    return failure


def _prepare_spec_bindings(
    *,
    ir_files: list[Path],
    artifact_dir: Path | None,
    compiler: str,
    temp_root: Path,
) -> tuple[list[SpecBinding], list[dict[str, Any]]]:
    bindings: list[SpecBinding] = []
    preflight_errors: list[dict[str, Any]] = []

    for ir_file in ir_files:
        spec: SpecIR | None = None
        try:
            raw = load_yaml(ir_file)
            spec, errors = validate_ir(raw)
            if spec is None:
                raise ValueError(f"Schema validation failed: {errors}")
            if errors:
                raise ValueError(f"Semantic validation failed: {errors}")

            project_name = spec.meta.name
            project_c_name = c_identifier(project_name)

            if artifact_dir is not None:
                header_name, source_name = protocol_output_filenames(spec, lang="c")
                source_path = artifact_dir / source_name
                header_path = artifact_dir / header_name
                if not source_path.exists():
                    raise FileNotFoundError(f"source artifact not found: {source_path}")
                if not header_path.exists():
                    raise FileNotFoundError(f"header artifact not found: {header_path}")
            else:
                generated_dir = temp_root / f"{project_c_name}_raw_gen"
                generated_files = generate_protocol(spec, str(generated_dir), lang="c")
                source_files = [path for path in generated_files if path.suffix == ".c"]
                header_files = [path for path in generated_files if path.suffix == ".h"]
                if len(source_files) != 1 or len(header_files) != 1:
                    raise ValueError(
                        f"expected one .c and one .h for generated artifacts, got: {generated_files}"
                    )
                source_path = source_files[0]
                header_path = header_files[0]

            library_path = temp_root / f"lib{project_c_name}_raw_roundtrip{_shared_library_suffix()}"
            _compile_shared_library(
                source_path=source_path,
                include_dir=source_path.parent,
                output_path=library_path,
                compiler=compiler,
            )
            lib = ctypes.CDLL(str(library_path))

            messages = [
                _build_message_binding(lib, spec, msg)
                for msg in sorted(spec.messages, key=lambda item: (item.id, item.name))
            ]
            if not messages:
                raise ValueError("no messages found in validated IR")

            bindings.append(
                SpecBinding(
                    spec=spec,
                    ir_path=ir_file,
                    project_name=project_name,
                    ir_version=spec.ir_version,
                    source_path=source_path,
                    header_path=header_path,
                    library_path=library_path,
                    messages=messages,
                )
            )
        except Exception as exc:
            preflight_errors.append(
                {
                    "timestamp_utc": utc_now_iso(),
                    "loop_index": None,
                    "seed": None,
                    "project_name": spec.meta.name if spec is not None else "*",
                    "ir_path": str(ir_file),
                    "ir_version": spec.ir_version if spec is not None else None,
                    "message_name": "*",
                    "encode_fn": "*",
                    "decode_fn": "*",
                    "property": "preflight",
                    "case_index": None,
                    "detail": str(exc),
                    "exception": str(exc),
                    "traceback": traceback.format_exc(),
                }
            )

    return bindings, preflight_errors


def _run_loop(
    *,
    loop_index: int,
    seed: int,
    cases_per_seed: int,
    bindings: list[SpecBinding],
) -> tuple[list[dict[str, Any]], int]:
    failures: list[dict[str, Any]] = []
    cases_run = 0

    for spec_index, spec_binding in enumerate(bindings):
        touched_encode: set[str] = set()
        touched_decode: set[str] = set()

        for msg_index, binding in enumerate(spec_binding.messages):
            rng = random.Random((seed << 20) ^ (spec_index << 10) ^ msg_index ^ binding.message.id)

            # raw_encode_decode_roundtrip
            for case_idx in range(cases_per_seed):
                cases_run += 1
                try:
                    original = _random_struct(binding, rng)
                    payload = (ctypes.c_uint8 * binding.message.dlc)()

                    encode_status = binding.encode_fn(payload, binding.message.dlc, ctypes.byref(original))
                    if encode_status != 0:
                        raise AssertionError(f"encode status={encode_status}")

                    decoded = binding.struct_type()
                    decode_status = binding.decode_fn(payload, binding.message.dlc, ctypes.byref(decoded))
                    if decode_status != 0:
                        raise AssertionError(f"decode status={decode_status}")

                    for field_name in binding.field_names:
                        if getattr(decoded, field_name) != getattr(original, field_name):
                            raise AssertionError(
                                f"field mismatch: {field_name} "
                                f"expected={getattr(original, field_name)} "
                                f"got={getattr(decoded, field_name)}"
                            )
                except Exception as exc:
                    failures.append(
                        _make_failure(
                            loop_index=loop_index,
                            seed=seed,
                            project_name=spec_binding.project_name,
                            ir_path=spec_binding.ir_path,
                            ir_version=spec_binding.ir_version,
                            message_name=binding.message.name,
                            encode_fn=binding.encode_name,
                            decode_fn=binding.decode_name,
                            property_name="raw_encode_decode_roundtrip",
                            case_index=case_idx,
                            detail=str(exc),
                            exc=exc,
                        )
                    )

                touched_encode.add(binding.encode_name)
                touched_decode.add(binding.decode_name)

            # raw_decode_encode_masked_roundtrip
            for case_idx in range(cases_per_seed):
                cases_run += 1
                try:
                    raw_bytes = [rng.randrange(0, 256) for _ in range(binding.message.dlc)]
                    payload_in = (ctypes.c_uint8 * binding.message.dlc)(*raw_bytes)

                    decoded = binding.struct_type()
                    decode_status = binding.decode_fn(payload_in, binding.message.dlc, ctypes.byref(decoded))
                    if decode_status != 0:
                        raise AssertionError(f"decode status={decode_status}")

                    payload_out = (ctypes.c_uint8 * binding.message.dlc)()
                    encode_status = binding.encode_fn(payload_out, binding.message.dlc, ctypes.byref(decoded))
                    if encode_status != 0:
                        raise AssertionError(f"encode status={encode_status}")

                    for bit_index in range(binding.message.dlc * 8):
                        got = _bit(payload_out, bit_index)
                        expected = _bit(payload_in, bit_index) if bit_index in binding.occupied_bits else 0
                        if got != expected:
                            raise AssertionError(f"bit mismatch at bit={bit_index}: expected={expected}, got={got}")
                except Exception as exc:
                    failures.append(
                        _make_failure(
                            loop_index=loop_index,
                            seed=seed,
                            project_name=spec_binding.project_name,
                            ir_path=spec_binding.ir_path,
                            ir_version=spec_binding.ir_version,
                            message_name=binding.message.name,
                            encode_fn=binding.encode_name,
                            decode_fn=binding.decode_name,
                            property_name="raw_decode_encode_masked_roundtrip",
                            case_index=case_idx,
                            detail=str(exc),
                            exc=exc,
                        )
                    )

                touched_encode.add(binding.encode_name)
                touched_decode.add(binding.decode_name)

        expected_encode = {binding.encode_name for binding in spec_binding.messages}
        expected_decode = {binding.decode_name for binding in spec_binding.messages}

        if touched_encode != expected_encode:
            failures.append(
                _make_failure(
                    loop_index=loop_index,
                    seed=seed,
                    project_name=spec_binding.project_name,
                    ir_path=spec_binding.ir_path,
                    ir_version=spec_binding.ir_version,
                    message_name="*",
                    encode_fn="*",
                    decode_fn="*",
                    property_name="raw_function_coverage",
                    case_index=None,
                    detail=f"encode coverage mismatch: touched={sorted(touched_encode)}, expected={sorted(expected_encode)}",
                )
            )
        if touched_decode != expected_decode:
            failures.append(
                _make_failure(
                    loop_index=loop_index,
                    seed=seed,
                    project_name=spec_binding.project_name,
                    ir_path=spec_binding.ir_path,
                    ir_version=spec_binding.ir_version,
                    message_name="*",
                    encode_fn="*",
                    decode_fn="*",
                    property_name="raw_function_coverage",
                    case_index=None,
                    detail=f"decode coverage mismatch: touched={sorted(touched_decode)}, expected={sorted(expected_decode)}",
                )
            )

    return failures, cases_run


def run_raw_roundtrip_campaign(
    *,
    ir_glob: str,
    artifact_dir: Path | None,
    compiler: str,
    loops: int,
    master_seed: int | None,
    seed_list_raw: str | None,
    cases_per_seed: int,
    report_dir: Path | None,
    test_file_name: str,
    continue_on_fail: bool = True,
) -> tuple[Path, Path | None, dict[str, Any]]:
    """Run seeded raw roundtrip campaign and emit YAML reports.

    Returns:
    - summary report path
    - error report path (or None)
    - summary report object
    """
    if loops < 1:
        raise ValueError("loops must be >= 1")
    if cases_per_seed < 1:
        raise ValueError("cases_per_seed must be >= 1")
    if shutil.which(compiler) is None:
        raise ValueError(f"compiler not found: {compiler}")

    resolved_artifact_dir = artifact_dir.resolve() if artifact_dir is not None else None
    resolved_report_dir = resolve_report_dir(report_dir, resolved_artifact_dir)

    run_stamp = utc_timestamp_slug()
    run_started_at = utc_now_iso()
    master = _resolve_master_seed(master_seed)
    explicit_seeds = _parse_seed_list(seed_list_raw)
    loop_seeds = _resolve_loop_seeds(loops=loops, master_seed=master, explicit_seeds=explicit_seeds)

    ir_files = _iter_ir_files(ir_glob)
    if not ir_files:
        raise ValueError(f"No .ir.yaml files found for glob: {ir_glob}")

    all_failures: list[dict[str, Any]] = []
    loop_summaries: list[dict[str, Any]] = []
    total_cases_run = 0

    with tempfile.TemporaryDirectory(prefix="specgo-raw-roundtrip-") as temp_dir:
        tmp_root = Path(temp_dir)
        bindings, preflight_errors = _prepare_spec_bindings(
            ir_files=ir_files,
            artifact_dir=resolved_artifact_dir,
            compiler=compiler,
            temp_root=tmp_root,
        )

        all_failures.extend(preflight_errors)

        for loop_index, seed in enumerate(loop_seeds):
            if not bindings:
                break
            loop_failures, cases_run = _run_loop(
                loop_index=loop_index,
                seed=seed,
                cases_per_seed=cases_per_seed,
                bindings=bindings,
            )
            total_cases_run += cases_run
            all_failures.extend(loop_failures)
            loop_summaries.append(
                {
                    "loop_index": loop_index,
                    "seed": seed,
                    "cases_run": cases_run,
                    "failure_count": len(loop_failures),
                    "status": "FAILED" if loop_failures else "PASSED",
                }
            )

            if loop_failures and not continue_on_fail:
                break

    input_specs = [
        {
            "project_name": binding.project_name,
            "ir_path": str(binding.ir_path),
            "ir_version": binding.ir_version,
            "source_path": str(binding.source_path),
            "header_path": str(binding.header_path),
        }
        for binding in bindings
    ]

    highlights = [
        {
            "loop_index": failure.get("loop_index"),
            "seed": failure.get("seed"),
            "project_name": failure.get("project_name"),
            "message_name": failure.get("message_name"),
            "property": failure.get("property"),
            "detail": failure.get("detail"),
        }
        for failure in all_failures[:20]
    ]

    total_loops_executed = len(loop_summaries)
    failed_loops = len([summary for summary in loop_summaries if summary["failure_count"] > 0])
    passed_loops = total_loops_executed - failed_loops
    status = "FAILED" if all_failures else "PASSED"

    summary_report = {
        "raw_roundtrip_run": {
            "run_stamp": run_stamp,
            "started_at_utc": run_started_at,
            "finished_at_utc": utc_now_iso(),
            "test_file_name": test_file_name,
            "toolchain": {
                "python_version": sys.version.split()[0],
                "platform": sys.platform,
                "compiler": compiler,
                "compiler_version": _compiler_version(compiler),
                "specgo_version": __version__,
            },
            "config": {
                "ir_glob": ir_glob,
                "artifact_dir": str(resolved_artifact_dir) if resolved_artifact_dir else None,
                "report_dir": str(resolved_report_dir),
                "loops": loops,
                "cases_per_seed": cases_per_seed,
                "continue_on_fail": continue_on_fail,
                "master_seed": master,
                "seed_list_input": explicit_seeds,
                "loop_seeds": loop_seeds,
            },
            "inputs": input_specs,
            "loop_summaries": loop_summaries,
            "summary": {
                "total_loops_executed": total_loops_executed,
                "passed_loops": passed_loops,
                "failed_loops": failed_loops,
                "total_cases_run": total_cases_run,
                "total_failures": len(all_failures),
                "status": status,
            },
            "raw_failure_highlights": highlights,
        }
    }

    error_report: dict[str, Any] | None = None
    if all_failures:
        error_report = {
            "raw_error_report": {
                "run_stamp": run_stamp,
                "generated_at_utc": utc_now_iso(),
                "test_file_name": test_file_name,
                "toolchain": {
                    "python_version": sys.version.split()[0],
                    "platform": sys.platform,
                    "compiler": compiler,
                    "compiler_version": _compiler_version(compiler),
                    "specgo_version": __version__,
                },
                "config": {
                    "ir_glob": ir_glob,
                    "artifact_dir": str(resolved_artifact_dir) if resolved_artifact_dir else None,
                    "report_dir": str(resolved_report_dir),
                    "loops": loops,
                    "cases_per_seed": cases_per_seed,
                    "continue_on_fail": continue_on_fail,
                    "master_seed": master,
                    "seed_list_input": explicit_seeds,
                    "loop_seeds": loop_seeds,
                },
                "inputs": input_specs,
                "master_seed": master,
                "total_failures": len(all_failures),
                "failures": all_failures,
            }
        }

    summary_path, error_path = write_raw_reports(
        report_dir=resolved_report_dir,
        run_stamp=run_stamp,
        summary_report=summary_report,
        error_report=error_report,
    )

    return summary_path, error_path, summary_report
