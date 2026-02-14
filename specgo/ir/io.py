# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""IR input/output and file validation utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import yaml

from specgo.ir.model import SpecIR


def validate_input_paths(inputs: Sequence[Path]) -> None:
    """Validate that all input paths exist and are files.

    Raises FileNotFoundError or ValueError on failure.
    """
    for inp in inputs:
        if not inp.exists():
            raise FileNotFoundError(f"Input file does not exist: {inp}")
        if not inp.is_file():
            raise ValueError(f"Input path is not a file: {inp}")


def validate_output_path(output: Path, num_inputs: int, force: bool) -> None:
    """Validate and prepare the output path.

    Rules:
    - Multiple inputs require output to be a directory.
    - Existing file: blocked unless force=True.
    - Existing dir: accepted.
    - Non-existent path: blocked unless force=True, then created
      (as dir if no suffix, parent dirs if suffix present).

    Raises FileExistsError, FileNotFoundError, or ValueError on failure.
    """
    if output.exists():
        if output.is_file():
            if num_inputs > 1:
                raise ValueError("Multiple inputs require --out to be a directory, not a file.")
            if not force:
                raise FileExistsError(f"Output file already exists: {output}")
        # existing dir is always fine
    else:
        if not force:
            raise FileNotFoundError(f"Output path does not exist: {output}")
        if output.suffix:
            output.parent.mkdir(parents=True, exist_ok=True)
        else:
            output.mkdir(parents=True, exist_ok=True)

    # Post-creation check: multiple inputs still needs a directory
    if num_inputs > 1 and not output.is_dir():
        raise ValueError("Multiple inputs require --out to be a directory, not a file.")


def validate_output_dir(output: Path) -> None:
    """Validate that the output path is a directory (not an existing file).

    Creates the directory (and parents) if it does not exist.
    Raises ValueError if the path is an existing file.
    """
    if output.is_file():
        raise ValueError(f"Output path is an existing file, expected a directory: {output}")
    output.mkdir(parents=True, exist_ok=True)


def resolve_output_file(input_path: Path, output: Path) -> Path:
    """Determine the actual output file path for a single input.

    If output is a directory, derive filename from input stem.
    Otherwise return output as-is.
    """
    if output.is_dir():
        return output / (input_path.stem + ".ir.yaml")
    return output


def dump_yaml(data: dict, output_path: Path) -> None:
    """Write a dict to a YAML file into the specified output path."""
    output_path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True, default_flow_style=False),
        encoding="utf-8",
        )


# Aliases for semantic clarity
dump_ir = dump_yaml


def load_yaml(path: Path) -> dict:
    """Load a YAML file and return a dict.

    Raises ValueError if the file is not valid YAML or not a mapping.
    """
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in {path}: {e}") from e

    if not isinstance(data, dict):
        raise ValueError(
            f"Expected a YAML mapping in {path}, got {type(data).__name__}"
        )
    return data


def load_ir(path: Path) -> SpecIR:
    """Load an .ir.yaml file into a SpecIR model.
    
    Raises ValueError if the file is not valid YAML or does not conform to the SpecIR schema.
    """
    # Note: model_validate isn't the validation check for IR, just for Pydantic schema. 
    return SpecIR.model_validate(load_yaml(path))
