from pathlib import Path

from preflight.inventory import inventory_build


def test_inventory_counts_files_and_bytes(tmp_path: Path) -> None:
    (tmp_path / "game.exe").write_bytes(b"game")
    data = tmp_path / "data"
    data.mkdir()
    (data / "asset.bin").write_bytes(b"123456")

    result = inventory_build(tmp_path)

    assert len(result.files) == 2
    assert result.total_bytes == 10
    assert result.coverage_complete


def test_symlink_is_not_followed_and_limits_coverage(tmp_path: Path) -> None:
    target = tmp_path / "real.txt"
    target.write_text("real")
    link = tmp_path / "linked.txt"
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError):
        return

    inventory = inventory_build(tmp_path)

    assert Path("linked.txt") in inventory.inaccessible
    assert inventory.coverage_complete is False
    assert all(record.relative_path != Path("linked.txt") for record in inventory.files)


def test_inventory_order_is_deterministic(tmp_path: Path) -> None:
    (tmp_path / "z.txt").write_text("z")
    (tmp_path / "a.txt").write_text("a")

    inventory = inventory_build(tmp_path)

    assert [record.relative_path for record in inventory.files] == [
        Path("a.txt"),
        Path("z.txt"),
    ]
