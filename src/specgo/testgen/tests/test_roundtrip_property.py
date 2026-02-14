# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""Seeded roundtrip property tests for generated protocol C code."""

from __future__ import annotations

import ctypes
import glob
import os
import random
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

from specgo.codegen.naming import c_identifier, protocol_message_symbols
from specgo.codegen.protocol import generate_protocol, protocol_output_filenames
from specgo.ir.io import load_yaml
from specgo.ir.model import Message, SpecIR
from specgo.ir.validator import validate_ir
from specgo.testgen.property import message_occupied_bits, random_raw_value


def _parse_seeds(raw: str) -> tuple[int, ...]:
    values = [item.strip() for item in raw.split(",")]
    seeds = tuple(int(item) for item in values if item)
    return seeds or (0,)


SEEDS = _parse_seeds(os.getenv("SPECGO_PROPTEST_SEEDS", "0,1,7,42,2026"))
CASES_PER_SEED = int(os.getenv("SPECGO_PROPTEST_CASES_PER_SEED", "2"))
COMPILER = os.getenv("SPECGO_PROPTEST_CC", "cl" if sys.platform == "win32" else "cc")
IR_GLOB = os.getenv("SPECGO_PROPTEST_IR_GLOB", "examples/output/*.ir.yaml")
ARTIFACT_DIR = os.getenv("SPECGO_PROPTEST_ARTIFACT_DIR")

if shutil.which(COMPILER) is None:
    pytest.skip(f"Compiler not found: {COMPILER}", allow_module_level=True)


@dataclass
class MessageBinding:
    message: Message
    struct_type: type[ctypes.Structure]
    encode_name: str
    decode_name: str
    encode_fn: ctypes._CFuncPtr
    decode_fn: ctypes._CFuncPtr
    field_names: list[str]
    occupied_bits: set[int]


@dataclass
class SpecBinding:
    spec: SpecIR
    ir_path: Path
    generated_dir: Path
    library_path: Path
    messages: list[MessageBinding]


def _shared_library_suffix() -> str:
    if sys.platform == "darwin":
        return ".dylib"
    if sys.platform == "win32":
        return ".dll"
    return ".so"


def _is_msvc(compiler: str) -> bool:
    """Check if the compiler is MSVC (cl.exe)."""
    return Path(compiler).stem.lower() == "cl"


def _compile_shared_library(source_path: Path, include_dir: Path, output_path: Path) -> None:
    if _is_msvc(COMPILER):
        cmd = [
            COMPILER, "/LD", "/std:c11", "/W4", "/WX",
            str(source_path), f"/I{include_dir}", "/link", f"/OUT:{output_path}",
        ]
        proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
        if proc.returncode == 0:
            return
        raise RuntimeError(
            f"Failed to compile generated source ({source_path.name}) with MSVC.\n"
            f"stderr: {proc.stderr}"
        )

    # GCC / Clang
    common = ["-std=c11", "-Wall", "-Wextra", "-Werror", str(source_path), f"-I{include_dir}", "-o", str(output_path)]

    primary = [COMPILER, "-shared", "-fPIC", *common]
    proc = subprocess.run(primary, check=False, capture_output=True, text=True)
    if proc.returncode == 0:
        return

    if sys.platform == "darwin":
        fallback = [COMPILER, "-dynamiclib", *common]
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


def _iter_ir_files() -> list[Path]:
    paths = [Path(p).resolve() for p in glob.glob(IR_GLOB, recursive=True)]
    return sorted(path for path in paths if path.suffix == ".yaml" and path.name.endswith(".ir.yaml"))


def _sorted_signals(msg: Message):
    return sorted(msg.signals, key=lambda item: (item.start_bit, item.name))


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
        struct_type=struct_type,
        encode_name=encode_name,
        decode_name=decode_name,
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


@pytest.fixture(scope="module")
def spec_bindings(tmp_path_factory: pytest.TempPathFactory) -> list[SpecBinding]:
    ir_files = _iter_ir_files()
    if not ir_files:
        pytest.skip(f"No .ir.yaml files found for glob: {IR_GLOB}")

    bindings: list[SpecBinding] = []
    for ir_file in ir_files:
        raw = load_yaml(ir_file)
        spec, errors = validate_ir(raw)
        assert spec is not None, f"Schema validation failed for {ir_file}: {errors}"
        assert not errors, f"Semantic validation failed for {ir_file}: {errors}"

        work_dir = tmp_path_factory.mktemp(f"roundtrip_{c_identifier(spec.meta.name)}")
        if ARTIFACT_DIR:
            generated_dir = Path(ARTIFACT_DIR).resolve()
            assert generated_dir.exists(), f"Artifact dir does not exist: {generated_dir}"
            assert generated_dir.is_dir(), f"Artifact dir is not a directory: {generated_dir}"
            header_name, source_name = protocol_output_filenames(spec, lang="c")
            source_files = [generated_dir / source_name]
            header_path = generated_dir / header_name
            assert source_files[0].exists(), (
                f"Source artifact not found for {ir_file}: {source_files[0]}"
            )
            assert header_path.exists(), (
                f"Header artifact not found for {ir_file}: {header_path}"
            )
        else:
            generated_dir = work_dir / "gen"
            generated_files = generate_protocol(spec, str(generated_dir), lang="c")
            source_files = [path for path in generated_files if path.suffix == ".c"]
            assert len(source_files) == 1, f"Expected exactly one generated source for {ir_file}"

        lib_path = work_dir / f"lib{c_identifier(spec.meta.name)}_protocol{_shared_library_suffix()}"
        _compile_shared_library(source_files[0], generated_dir, lib_path)
        lib = ctypes.CDLL(str(lib_path))

        message_bindings = [
            _build_message_binding(lib, spec, msg)
            for msg in sorted(spec.messages, key=lambda item: (item.id, item.name))
        ]
        assert message_bindings, f"No messages found in IR: {ir_file}"

        bindings.append(
            SpecBinding(
                spec=spec,
                ir_path=ir_file,
                generated_dir=generated_dir,
                library_path=lib_path,
                messages=message_bindings,
            )
        )

    return bindings


@pytest.mark.parametrize("seed", SEEDS)
def test_roundtrip_encode_then_decode(spec_bindings: list[SpecBinding], seed: int) -> None:
    """Property: decode(encode(struct)) == struct for all messages."""
    for spec_binding in spec_bindings:
        touched_encode: set[str] = set()
        touched_decode: set[str] = set()

        for msg_index, binding in enumerate(spec_binding.messages):
            rng = random.Random((seed << 16) ^ msg_index ^ binding.message.id)
            for _ in range(CASES_PER_SEED):
                original = _random_struct(binding, rng)

                payload = (ctypes.c_uint8 * binding.message.dlc)()
                encode_status = binding.encode_fn(payload, binding.message.dlc, ctypes.byref(original))
                assert encode_status == 0, (
                    f"Encode failed: {binding.encode_name} "
                    f"(msg={binding.message.name}, seed={seed}) -> status={encode_status}"
                )

                decoded = binding.struct_type()
                decode_status = binding.decode_fn(payload, binding.message.dlc, ctypes.byref(decoded))
                assert decode_status == 0, (
                    f"Decode failed: {binding.decode_name} "
                    f"(msg={binding.message.name}, seed={seed}) -> status={decode_status}"
                )

                for field_name in binding.field_names:
                    assert getattr(decoded, field_name) == getattr(original, field_name), (
                        f"Roundtrip mismatch: {binding.message.name}.{field_name} "
                        f"(seed={seed})"
                    )

                touched_encode.add(binding.encode_name)
                touched_decode.add(binding.decode_name)

        expected_encode = {binding.encode_name for binding in spec_binding.messages}
        expected_decode = {binding.decode_name for binding in spec_binding.messages}
        assert touched_encode == expected_encode
        assert touched_decode == expected_decode


@pytest.mark.parametrize("seed", SEEDS)
def test_roundtrip_decode_then_encode_masked_payload(spec_bindings: list[SpecBinding], seed: int) -> None:
    """Property: encode(decode(payload)) preserves occupied bits and zeroes unoccupied bits."""
    for spec_binding in spec_bindings:
        touched_encode: set[str] = set()
        touched_decode: set[str] = set()

        for msg_index, binding in enumerate(spec_binding.messages):
            rng = random.Random((seed << 20) ^ msg_index ^ (binding.message.id << 1))
            for _ in range(CASES_PER_SEED):
                raw_bytes = [rng.randrange(0, 256) for _ in range(binding.message.dlc)]
                payload_in = (ctypes.c_uint8 * binding.message.dlc)(*raw_bytes)

                decoded = binding.struct_type()
                decode_status = binding.decode_fn(payload_in, binding.message.dlc, ctypes.byref(decoded))
                assert decode_status == 0, (
                    f"Decode failed: {binding.decode_name} "
                    f"(msg={binding.message.name}, seed={seed}) -> status={decode_status}"
                )

                payload_out = (ctypes.c_uint8 * binding.message.dlc)()
                encode_status = binding.encode_fn(payload_out, binding.message.dlc, ctypes.byref(decoded))
                assert encode_status == 0, (
                    f"Encode failed after decode: {binding.encode_name} "
                    f"(msg={binding.message.name}, seed={seed}) -> status={encode_status}"
                )

                for bit_index in range(binding.message.dlc * 8):
                    got = _bit(payload_out, bit_index)
                    if bit_index in binding.occupied_bits:
                        expected = _bit(payload_in, bit_index)
                    else:
                        expected = 0
                    assert got == expected, (
                        f"Masked payload mismatch: {binding.message.name} bit={bit_index} "
                        f"(seed={seed})"
                    )

                touched_encode.add(binding.encode_name)
                touched_decode.add(binding.decode_name)

        expected_encode = {binding.encode_name for binding in spec_binding.messages}
        expected_decode = {binding.decode_name for binding in spec_binding.messages}
        assert touched_encode == expected_encode
        assert touched_decode == expected_decode
