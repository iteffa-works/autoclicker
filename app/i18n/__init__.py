"""UI strings: EN / UK / RU JSON bundles."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_DIR = Path(__file__).resolve().parent

_VALID = frozenset({"en", "uk", "ru"})


def normalize_ui_language(raw: str) -> str:
    s = (raw or "").strip().lower().replace("-", "_")
    if s in ("ua", "uk"):
        return "uk"
    if s in ("en", "eng"):
        return "en"
    if s in ("ru", "rus"):
        return "ru"
    if s in _VALID:
        return s
    return "uk"


@lru_cache(maxsize=8)
def _load(lang: str) -> dict[str, Any]:
    lang = normalize_ui_language(lang)
    path = _DIR / f"{lang}.json"
    if not path.is_file():
        path = _DIR / "uk.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def tr(lang: str, key: str) -> str:
    """Nested key path (e.g. app.product_subtitle, kb_test.history). Falls back to uk, then to key."""
    parts = key.split(".")
    for lg in (normalize_ui_language(lang), "uk"):
        data = _load(lg)
        cur: Any = data
        ok = True
        for p in parts:
            if isinstance(cur, dict) and p in cur:
                cur = cur[p]
            else:
                ok = False
                break
        if ok and isinstance(cur, str):
            return cur
    return key


def tr_kb(lang: str, key: str) -> str:
    """Alias for keyboard-test strings (same as tr)."""
    return tr(lang, key)
