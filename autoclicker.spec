# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller one-file spec (portable single .exe)."""

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files

root = Path(SPECPATH).resolve()

block_cipher = None

a = Analysis(
    [str(root / "main.py")],
    pathex=[str(root)],
    binaries=[],
    datas=[
        (str(root / "config" / "settings.example.json"), "config"),
        (str(root / "config" / "clicker.example.json"), "config"),
        (str(root / "config" / "binds.example.json"), "config"),
        (str(root / "config" / "macros.example.json"), "config"),
        (str(root / "config" / "plugin.json"), "config"),
        (str(root / "data" / "macros" / "example_macro.json"), "data/macros"),
        (str(root / "assets" / "icons"), "assets/icons"),
        (str(root / "assets" / "images"), "assets/images"),
    ]
    + [(str(p), "app/i18n") for p in (root / "app" / "i18n").glob("*.json")]
    + collect_data_files("qtawesome"),
    hiddenimports=["pynput.keyboard._win32", "pynput.mouse._win32", "qtawesome"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="autoclicker",
    icon=str(root / "assets" / "icons" / "favicon.ico"),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    # UPX іноді псує відображення іконки .exe у Провіднику Windows
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
