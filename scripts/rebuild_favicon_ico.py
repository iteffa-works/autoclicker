"""Regenerate assets/icons/favicon.ico from favicon.png (multi-size for Windows/PyInstaller)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PNG = ROOT / "assets" / "icons" / "favicon.png"
ICO = ROOT / "assets" / "icons" / "favicon.ico"


def main() -> None:
    im = Image.open(PNG).convert("RGBA")
    ICO.parent.mkdir(parents=True, exist_ok=True)
    im.save(
        ICO,
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    print(ICO, ICO.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
