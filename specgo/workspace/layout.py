# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""Workspace layout — directory structure conventions.

TODO: Define and manage the standard project directory layout
(specs/, ir/, gen/, reports/, replay/, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class WorkspaceLayout:
    """Defines the standard directory layout for a SpecGo workspace.

    TODO: Expand with methods to initialize and resolve paths.
    """

    root: Path

    @property
    def specs_dir(self) -> Path:
        return self.root / "specs"

    @property
    def ir_dir(self) -> Path:
        return self.root / "ir"

    @property
    def gen_dir(self) -> Path:
        return self.root / "gen"

    @property
    def reports_dir(self) -> Path:
        return self.root / "reports"

    @property
    def replay_dir(self) -> Path:
        return self.root / "replay"

    def init(self) -> None:
        """Create all workspace directories.

        TODO: Implement.
        """
        raise NotImplementedError("Workspace init not implemented")
