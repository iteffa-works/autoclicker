"""Filesystem paths: portable layout next to executable when frozen."""

from __future__ import annotations

import sys
from pathlib import Path


def _project_root_dev() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent.parent


def app_base_dir() -> Path:
    """Directory where config/ and data/ live (next to .exe in PyInstaller onefile)."""
    return _project_root_dev()


def config_dir() -> Path:
    p = app_base_dir() / "config"
    p.mkdir(parents=True, exist_ok=True)
    return p


def data_dir() -> Path:
    p = app_base_dir() / "data"
    p.mkdir(parents=True, exist_ok=True)
    return p


def macros_dir() -> Path:
    p = data_dir() / "macros"
    p.mkdir(parents=True, exist_ok=True)
    return p


def settings_path() -> Path:
    return config_dir() / "settings.json"


def assets_dir() -> Path:
    if getattr(sys, "frozen", False):
        me = getattr(sys, "_MEIPASS", None)
        if me:
            return Path(me) / "assets"
    return app_base_dir() / "assets"
