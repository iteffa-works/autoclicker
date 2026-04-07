from pathlib import Path

from app.utils.json_io import read_json


def test_read_json_returns_default_for_invalid_json(tmp_path: Path) -> None:
    broken = tmp_path / "broken.json"
    broken.write_text("{not valid json", encoding="utf-8")

    assert read_json(broken, {"ok": True}) == {"ok": True}
