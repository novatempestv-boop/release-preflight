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
