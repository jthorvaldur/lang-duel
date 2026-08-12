#!/usr/bin/env python3
"""Lucha Léxica launcher — the game lives in the lucha package.

Run:  ./duelo.py   ·   ./duelo.py --check validates the content pack.
Content edits: lucha/content/es-en/*.json — see AGENTS.md for schemas.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lucha.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
