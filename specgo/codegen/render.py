# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""Jinja2 rendering helpers for code generation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined


TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"


def create_template_env(template_dir: Path | None = None) -> Environment:
    """Create a strict Jinja2 environment."""
    root = template_dir or TEMPLATE_DIR
    return Environment(
        loader=FileSystemLoader(str(root)),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
        undefined=StrictUndefined,
    )


def render_template(
    template_name: str,
    context: dict[str, Any],
    template_dir: Path | None = None,
) -> str:
    """Render a template into text."""
    env = create_template_env(template_dir)
    template = env.get_template(template_name)
    return template.render(**context)


def render_to_file(
    template_name: str,
    context: dict[str, Any],
    output_path: Path,
    template_dir: Path | None = None,
) -> None:
    """Render a template and write it to file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        render_template(template_name, context, template_dir=template_dir),
        encoding="utf-8",
    )
