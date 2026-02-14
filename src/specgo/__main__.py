# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""Module entrypoint for `python -m SpecGo`."""

from specgo.cli import app

def run():
    """Run SpecGo."""
    app()

if __name__ == "__main__":
    run()
