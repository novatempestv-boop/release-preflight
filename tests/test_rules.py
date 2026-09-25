from pathlib import Path

from preflight.inventory import inventory_build
from preflight.rules import inspect


def test_initial_rules_find_release_leftovers(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("SECRET=hidden")
    (tmp_path / "debug.log").write_text("hello")
    (tmp_path / "art.psd").write_bytes(b"source")
    (tmp_path / ".DS_Store").write_bytes(b"junk")

    findings = inspect(inventory_build(tmp_path))

    assert [f.severity for f in findings] == ["Critical", "Warning", "Warning", "Info"]
