from pathlib import Path

from preflight.analysis import duplicate_groups
from preflight.inventory import inventory_build


def test_exact_duplicates_are_grouped_and_waste_is_counted(tmp_path: Path) -> None:
    payload = b"x" * 2048
    (tmp_path / "a.bin").write_bytes(payload)
    (tmp_path / "b.bin").write_bytes(payload)
    (tmp_path / "different.bin").write_bytes(b"y" * 2048)

    groups = duplicate_groups(inventory_build(tmp_path), minimum_size=1024)

    assert len(groups) == 1
    assert groups[0].paths == (Path("a.bin"), Path("b.bin"))
    assert groups[0].wasted_bytes == 2048


def test_small_duplicates_are_ignored(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("same")
    (tmp_path / "b.txt").write_text("same")

    assert duplicate_groups(inventory_build(tmp_path)) == ()
