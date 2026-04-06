"""Alternate entry: `python app.py` (package `app/` remains the main codebase)."""

from __future__ import annotations

from app.bootstrap import main

if __name__ == "__main__":
    raise SystemExit(main())
