from pathlib import Path

from preflight.analysis import composition, largest_files
from preflight.inventory import inventory_build


def test_composition_and_largest_files(tmp_path: Path) -> None:
    (tmp_path / "game.exe").write_bytes(b"x" * 10)
    (tmp_path / "music.ogg").write_bytes(b"x" * 20)
    (tmp_path / "movie.mp4").write_bytes(b"x" * 30)

    inventory = inventory_build(tmp_path)
    stats = composition(inventory)

    assert [(s.name, s.bytes) for s in stats] == [
        ("Video", 30),
        ("Audio", 20),
        ("Executables", 10),
    ]
    assert largest_files(inventory, 1)[0].relative_path == Path("movie.mp4")
