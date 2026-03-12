# SpecGo

**Spec → IR → Codegen → Gate → Test → Report**

SpecGo is a CLI-first toolchain that turns embedded communication protocol specifications (CAN DBC) into a unified **Spec IR**, generates verified protocol encoder/decoder code (C), and validates every artifact through deterministic **quality gates** and **seeded property tests**.

## Why SpecGo?

Protocol implementations (encoder/decoder, bit packing, endianness) are error-prone and hard to verify against the original specification. Code generation without a verification loop just produces bugs faster.

**Core principle:** Generate + Gate + Verify — every artifact must pass through deterministic gates before it counts as "done".

## Architecture

```
┌──────────────┐     ┌──────────┐     ┌──────────┐     ┌───────────┐     ┌──────────┐
│  Spec Files  │────▶│  Ingest  │────▶│  Spec IR │────▶│  Codegen  │────▶│  Output  │
│    .dbc      │     │ cantools │     │  (.yaml) │     │ (Jinja2)  │     │  .c / .h │
└──────────────┘     └──────────┘     └────┬─────┘     └───────────┘     └────┬─────┘
                                           │                                  │
                                     ┌─────▼──────┐                     ┌─────▼─────┐
                                     │ Validator  │                     │   Gates   │
                                     │ L0 Schema  │                     │ Codegen + │
                                     │ L1 Semantic│                     │ Roundtrip │
                                     └────────────┘                     └───────────┘
```

**IR is the center** — the spec is first converted into a structured, versionable, diffable IR. All downstream steps operate on IR.

**Validation first** — Pydantic schema validation is the entry point. Semantic checks cover DLC bounds, bit overlap, endianness layout, enum range, and scale correctness.

**Gates are mandatory** — codegen artifacts are gated (deterministic hash, file presence, compile syntax), then verified by seeded roundtrip property tests.

## Current Status

| Component | Status |
|-----------|--------|
| DBC → IR ingestion (`cantools`) | Done |
| IR model (Pydantic v2) | Done |
| Layer 0: Schema validation | Done |
| Layer 1: Semantic validation (DLC, bit overlap, enum, scale, endianness) | Done |
| Protocol codegen (Jinja2, C encode/decode) | Done |
| Codegen gate (deterministic hash, file presence, compile syntax) | Done |
| Seeded roundtrip property tests (encode/decode verification) | Done |
| CLI commands (`ingest`, `validate`, `proto-codegen`, `gate-codegen`, `test-roundtrip`, `start`, `config`) | Done |
| Workspace bootstrap & config management (global + project scope) | Done |
| Cross-platform compilation (GCC/Clang + MSVC) | Done |
| YAML report generation (summary + error reports) | Done |
| PDF / Text ingest | Planned |
| Multi-language codegen (C++, Python, Rust) | Planned |
| API wrapper / platform adapter codegen | Planned |
| Agent pipeline orchestration (LLM-assisted) | Planned |
| Differential testing (`test-diff`) | Planned |

## Update Log

### v1.0.1 (2026-03-12) - First Stable Release

- First public stable release of SpecGo.
- End-to-end deterministic pipeline available: `ing` -> `val` -> `gen` -> `gate` -> `rt`.
- DBC ingest, IR schema/semantic validation, C protocol codegen, and codegen gates are production-ready.
- Seeded raw roundtrip property testing and YAML report output are included by default.
- Workspace bootstrap (`start`) and scoped config (`config`, `-g config`) are available.
- LLM/Agent config fields are reserved for future integration; advanced LLM-assisted flow is still planned.

## Quickstart

```bash
pip install -U pip
pip install typer pyyaml pydantic cantools jinja2
pip install -U typer pyyaml pydantic cantools jinja2
```

```bash
pip install -i https://test.pypi.org/simple/ SpecGo
pip install SpecGo
```

```bash
pip install -e .
```

```bash
specgo start
specgo --help
```

## Recommended Command Flow (Ordered)

Use this sequence for a deterministic pipeline from spec to verified artifacts.

### 1) Initialize workspace/config

```bash
# initialize global + project workspace metadata
specgo start
```

### 2) Ingest spec file to IR

```bash
# input: your .dbc
# output: specgo_output/output/<name>.ir.yaml
specgo ing path/to/your.dbc -f
```

### 3) Validate IR (Layer 0 + Layer 1)

```bash
# output: <ir>.validation.yaml
specgo val specgo_output/output/your.ir.yaml
```

### 4) Generate protocol C/H

```bash
# output: specgo_output/gen/<name>_protocol.c/.h
specgo gen specgo_output/output/your.ir.yaml
```

### 5) Run codegen gate (determinism + file checks + compile syntax)

```bash
specgo gate specgo_output/output/your.ir.yaml
```

### 6) Run seeded roundtrip tests (raw encode/decode checks)

```bash
# default: loops=10, continue-on-fail
# reports: specgo_output/raw_reports/
specgo rt -n 10
```

### 7) (Planned) Differential test for wrapper/AI-augmented layers

```bash
# reserved for future wrapper-vs-baseline behavior comparison
specgo diff
```

Recommended order summary: `start` → `ing` → `val` → `gen` → `gate` → `rt` → `diff(planned)`

## Verifiable Templates

The `examples/` folder provides sanitized verification templates for quick checks.

### 1) Valid DBC (ingest + validate should pass)

```bash
specgo ing examples/template_valid_sanitized.dbc -f
specgo val specgo_output/output/template_valid_sanitized.ir.yaml
```

### 2) Semantic-fail DBC (validate should fail by design)

```bash
specgo ing examples/template_invalid_semantic_sanitized.dbc -f
specgo val specgo_output/output/template_invalid_semantic_sanitized.ir.yaml
```

Expected failure reason: Layer-1 semantic check reports `scale is 0`.

### 3) Roundtrip mismatch demo (encode/decode intentionally inconsistent)

```bash
specgo ing examples/template_roundtrip_mismatch_sanitized.dbc -f
specgo val specgo_output/output/template_roundtrip_mismatch_sanitized.ir.yaml
specgo rt \
  --ir-glob specgo_output/output/template_roundtrip_mismatch_sanitized.ir.yaml \
  --artifact-dir examples/roundtrip_mismatch_artifacts \
  -n 1 -c 2 --stop-on-fail
```

Expected result: roundtrip run exits with `FAILED` and writes error reports.

Note: generated reports may contain local absolute paths; keep runtime outputs out of git.

## CLI Commands

| Command | Description |
|---------|-------------|
| `specgo ingest` / `specgo ing` | Parse DBC file and emit IR YAML (`specgo_output/output` by default) |
| `specgo validate` / `specgo val` | Run Layer 0 + Layer 1 validation, emit `.ir.validation.yaml` |
| `specgo proto-codegen` / `specgo gen` | Generate C protocol encoder/decoder from IR |
| `specgo gate-codegen` / `specgo gate` | Verify codegen artifacts (hash, presence, compile) |
| `specgo test-roundtrip` / `specgo rt` | Run seeded roundtrip property tests on generated code |
| `specgo test-diff` / `specgo diff` | Differential test entry (planned) |
| `specgo start` / `specgo init` | Discover project root and initialize workspace/bootstrap metadata |
| `specgo config` / `specgo cfg` / `specgo -g config` | Show or update project/global config |
| `specgo run` / `specgo go` | Full agent pipeline (planned) |

Default output paths (when no custom paths are given):

| Path | Content |
|------|---------|
| `specgo_output/output/` | Imported IR YAML files |
| `specgo_output/gen/` | Generated C/H artifacts |
| `specgo_output/raw_reports/` | Roundtrip test reports |
| `specgo_output/reports/` | Diff-test outputs (planned) |

## Workspace & Config

`specgo start` bootstraps the workspace:
- Auto-scans upward for project root (`.git`)
- Creates global config at `~/.specgo/config` (first-time interactive dialog)
- Creates project workspace at `<project>/.specgo/` with `config` and `run` metadata files

`specgo config` manages configuration:
- Project scope (default): reads/writes `<project>/.specgo/config`
- Global scope (`-g`): reads/writes `~/.specgo/config`
- Set values: `--set key=value` (supports dotted keys like `llm.provider=openai`)
- Workspace directory name is locked to `.specgo`

Note: LLM/Agent fields shown during `specgo start` initialization are placeholders for future integration and are not functionally wired yet.

## Pipeline: Gate → Test Responsibilities

- **`gate-codegen`** — artifact gate for protocol codegen output (`.h/.c`):
  - Deterministic generation check (re-generate and compare hashes)
  - Expected file presence validation
  - Compile syntax gate (GCC/Clang on Linux/macOS, MSVC on Windows)

- **`test-roundtrip`** — seeded randomized property tests for `encode`/`decode`:
  - Verifies every generated protocol function against IR signal semantics
  - Encode → decode roundtrip: `decode(encode(struct)) == struct`
  - Decode → encode masked payload: occupied bits preserved, unoccupied bits zeroed
  - Can run directly on already-gated artifacts via `--artifact-dir`
  - Reports persisted as YAML with full reproducibility info

Recommended order: `val` → `gen` → `gate` → `rt`

## Roundtrip Testing

Reports:

- Summary: `<timestamp>-raw.report.yaml` (always emitted)
- Errors: `<timestamp>-raw.error.report.yaml` (on failures)
- Default location: `specgo_output/raw_reports/`
- `master_seed` and `loop_seeds` always persisted for exact reproduction
- `--continue-on-fail` (default) / `--stop-on-fail` for fail-fast

## Spec IR Model

Pydantic v2 model serialized to YAML:

```yaml
ir_version: '0.1'
meta:
  name: FILE_NAME
  version: unknown
  source: DIR/FILE_NAME.dbc
  format: dbc
bus_type:
  bustype: CAN
  busmode: classic
messages:
  - id: 34
    name: XXXXMSG
    dlc: 8
    signals:
      - name: XXXXXXError
        start_bit: 0
        bit_length: 1
        byte_order: little_endian
        signed: false
        scale: 1.0
        offset: 0.0
        enum:
          - name: "No Fault"
            value: 0
          - name: "Fault Present"
            value: 1
```

## Validation Layers

- **Layer 0 (Schema):** Pydantic model validation — types, required fields, constraints
- **Layer 1 (Semantic):**
  - Signal bits fit within message DLC (little-endian and big-endian/Motorola)
  - No overlapping signal bit ranges
  - Default values within [min, max]
  - Enum values fit within bit_length (signed/unsigned aware)
  - Scale is not zero
  - min < max when both are set

## Known Limitations

- Enum metadata exists in IR but is not emitted as C `enum`/constants in generated code.
- Signal storage is fixed to 64-bit integer types (`uint64_t` / `int64_t`).
- Generated code encodes/decodes **raw** signal values only (scale/offset preserved as metadata comments, physical-value conversion not yet implemented).

## Project Structure

```
specgo/
├── cli/                         # Typer CLI
│   ├── main.py                  # App entry point, global flags
│   ├── default_paths.py         # Shared default output paths
│   └── commands/
│       ├── start.py             #   specgo start / init
│       ├── config.py            #   specgo config / cfg
│       ├── spec_ingest.py       #   specgo ingest / ing
│       ├── spec_validate.py     #   specgo validate / val
│       ├── codegen_protocol.py  #   specgo proto-codegen / gen
│       ├── gate_codegen.py      #   specgo gate-codegen / gate
│       ├── test_roundtrip.py    #   specgo test-roundtrip / rt
│       ├── test_diff.py         #   specgo test-diff / diff (planned)
│       └── run.py               #   specgo run / go (planned)
├── ir/                          # Intermediate Representation
│   ├── model.py                 # SpecIR / Message / Signal (Pydantic v2)
│   ├── io.py                    # YAML I/O, path validation utilities
│   └── validator/
│       ├── layer0_schema.py     #   Pydantic schema check
│       └── layer1_semantic.py   #   Semantic cross-field checks
├── ingest/                      # Spec file converters
│   ├── dispatcher.py            # Route by file extension
│   └── dbc.py                   # DBC → IR (via cantools)
├── codegen/                     # Code generation
│   ├── protocol.py              # Protocol encoder/decoder codegen
│   ├── naming.py                # C identifier / symbol naming policy
│   ├── render.py                # Jinja2 template rendering
│   └── templates/c/
│       ├── protocol.h.j2        #   Header (structs, prototypes, macros)
│       └── protocol.c.j2        #   Source (bit-level encode/decode)
├── gates/                       # Quality gate evaluation
│   ├── codegen.py               # Codegen artifact gates (hash, compile)
│   ├── evaluator.py             # Gate threshold evaluation
│   ├── metrics.py               # Gate metrics models
│   └── io.py                    # Gate I/O helpers
├── testgen/                     # Test generation & execution
│   ├── property.py              # Signal bit helpers, random value gen
│   ├── raw/
│   │   ├── runner.py            #   Campaign runner (compile, test, report)
│   │   └── io.py                #   Report I/O
│   └── tests/
│       └── test_roundtrip_property.py
└── workspace/                   # Workspace & config management
    ├── bootstrap.py             # Project/global workspace bootstrap
    └── config_model.py          # Pydantic config models (Global, Project, RunState)
```

## Dependencies

- Python >= 3.11
- [Pydantic](https://docs.pydantic.dev/) >= 2.0 — IR model & validation
- [cantools](https://github.com/cantools/cantools) >= 39.0 — DBC parsing
- [Typer](https://typer.tiangolo.com/) >= 0.12 — CLI framework
- [PyYAML](https://pyyaml.org/) >= 6.0 — IR serialization
- [Jinja2](https://jinja.palletsprojects.com/) >= 3.1.2 — Code generation templates
- C compiler (GCC/Clang or MSVC) — required for gate-codegen and test-roundtrip

## License

Apache-2.0. See [LICENSE](LICENSE).
