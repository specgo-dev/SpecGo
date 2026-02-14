# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""Report IO helpers for raw roundtrip campaigns."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


def utc_now_iso() -> str:
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def utc_timestamp_slug() -> str:
    """Return filesystem-safe UTC timestamp for report filenames."""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def resolve_report_dir(report_dir: Path | None, artifact_dir: Path | None) -> Path:
    """Resolve output directory for raw reports.

    Default behavior:
    - if report_dir provided: use it
    - elif artifact_dir provided: use sibling dir named `raw_reports`
    - else: use cwd sibling to default `gen`, i.e. `./raw_reports`
    """
    if report_dir is not None:
        return report_dir

    if artifact_dir is not None:
        return artifact_dir.resolve().parent / "raw_reports"

    return (Path.cwd() / "raw_reports").resolve()


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    """Write YAML to file with stable formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            data,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
        ),
        encoding="utf-8",
    )


def write_raw_reports(
    *,
    report_dir: Path,
    run_stamp: str,
    summary_report: dict[str, Any],
    error_report: dict[str, Any] | None,
) -> tuple[Path, Path | None]:
    """Write summary and optional error report files."""
    summary_path = report_dir / f"{run_stamp}-raw.report.yaml"
    write_yaml(summary_path, summary_report)

    error_path: Path | None = None
    if error_report is not None:
        error_path = report_dir / f"{run_stamp}-raw.error.report.yaml"
        write_yaml(error_path, error_report)

    return summary_path, error_path
