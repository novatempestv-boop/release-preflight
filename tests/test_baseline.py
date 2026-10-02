from pathlib import Path

from preflight.baseline import diff_snapshots, snapshot_inventory
from preflight.inventory import inventory_build


def test_snapshot_diff_tracks_added_removed_and_size_changes(tmp_path: Path) -> None:
    build = tmp_path / "build"
    build.mkdir()
    (build / "same.txt").write_text("same", encoding="utf-8")
    (build / "changed.bin").write_bytes(b"old")
    (build / "removed.txt").write_text("gone", encoding="utf-8")

    previous = snapshot_inventory(inventory_build(build))

    (build / "changed.bin").write_bytes(b"much larger")
    (build / "removed.txt").unlink()
    (build / "added.txt").write_text("new", encoding="utf-8")

    current = snapshot_inventory(inventory_build(build))
    diff = diff_snapshots(previous, current)

    assert [item.path for item in diff.added] == ["added.txt"]
    assert [item.path for item in diff.removed] == ["removed.txt"]
    assert [(old.path, new.path) for old, new in diff.size_changed] == [
        ("changed.bin", "changed.bin")
    ]
    assert diff.unchanged == 1
    assert diff.bytes_delta == current.total_bytes - previous.total_bytes


def test_baseline_round_trip_is_portable_and_content_free(tmp_path: Path) -> None:
    from preflight.baseline import load_baseline, save_baseline

    build = tmp_path / "build"
    build.mkdir()
    nested = build / "assets"
    nested.mkdir()
    (nested / "hero.bin").write_bytes(b"abc")

    snapshot = snapshot_inventory(inventory_build(build))
    baseline_path = tmp_path / "baseline.json"
    save_baseline(snapshot, baseline_path)

    text = baseline_path.read_text(encoding="utf-8")
    assert "assets/hero.bin" in text
    assert str(build) not in text
    assert "abc" not in text
    assert load_baseline(baseline_path) == snapshot
