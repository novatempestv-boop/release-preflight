from pathlib import Path

from preflight.baseline import diff_snapshots, load_baseline, save_baseline, snapshot_inventory
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


def test_baseline_diff_can_show_added_removed_and_changed_sections(tmp_path: Path) -> None:
    build = tmp_path / "build"
    build.mkdir()
    (build / "same.txt").write_text("same", encoding="utf-8")
    (build / "changed.bin").write_bytes(b"old")
    (build / "removed.txt").write_text("gone", encoding="utf-8")

    baseline_path = tmp_path / "baseline.json"
    save_baseline(snapshot_inventory(inventory_build(build)), baseline_path)

    (build / "changed.bin").write_bytes(b"new and larger")
    (build / "removed.txt").unlink()
    (build / "added.txt").write_text("new", encoding="utf-8")

    diff = diff_snapshots(
        load_baseline(baseline_path),
        snapshot_inventory(inventory_build(build)),
    )

    assert [item.path for item in diff.added] == ["added.txt"]
    assert [item.path for item in diff.removed] == ["removed.txt"]
    assert len(diff.size_changed) == 1
    assert diff.size_changed[0][0].path == "changed.bin"
    assert diff.size_changed[0][1].path == "changed.bin"


def test_diff_explains_size_change_by_top_level_area(tmp_path: Path) -> None:
    build = tmp_path / "build"
    (build / "audio").mkdir(parents=True)
    (build / "art").mkdir()
    (build / "audio" / "theme.ogg").write_bytes(b"1234")
    (build / "art" / "hero.png").write_bytes(b"12")

    previous = snapshot_inventory(inventory_build(build))

    (build / "audio" / "theme.ogg").write_bytes(b"123456789")
    (build / "art" / "extra.png").write_bytes(b"123")

    current = snapshot_inventory(inventory_build(build))
    diff = diff_snapshots(previous, current)

    assert diff.bytes_delta == 8
    assert diff.growth_by_top_level == (("audio", 5), ("art", 3))


def test_fingerprinted_baseline_detects_same_size_content_change(tmp_path: Path) -> None:
    build = tmp_path / "build"
    build.mkdir()
    file = build / "game.bin"
    file.write_bytes(b"AAAA")

    previous = snapshot_inventory(inventory_build(build), include_fingerprints=True)
    save_baseline(previous, tmp_path / "baseline.json")

    file.write_bytes(b"BBBB")
    current = snapshot_inventory(inventory_build(build), include_fingerprints=True)
    diff = diff_snapshots(load_baseline(tmp_path / "baseline.json"), current, verify_content=True)

    assert diff.size_changed == ()
    assert [(old.path, new.path) for old, new in diff.content_changed] == [
        ("game.bin", "game.bin")
    ]
    assert diff.content_unverified == ()
    assert diff.unchanged == 0


def test_unfingerprinted_baseline_never_claims_content_is_unchanged(tmp_path: Path) -> None:
    build = tmp_path / "build"
    build.mkdir()
    (build / "game.bin").write_bytes(b"AAAA")

    previous = snapshot_inventory(inventory_build(build))
    current = snapshot_inventory(inventory_build(build), include_fingerprints=True)

    diff = diff_snapshots(previous, current, verify_content=True)

    assert diff.content_changed == ()
    assert [item.path for item in diff.content_unverified] == ["game.bin"]
    assert diff.unchanged == 0
