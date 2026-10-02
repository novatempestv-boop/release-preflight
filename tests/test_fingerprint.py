from pathlib import Path

from preflight.fingerprint import fingerprint_file


def test_fingerprint_detects_same_size_content_change(tmp_path: Path) -> None:
    file = tmp_path / "game.bin"
    file.write_bytes(b"AAAA")
    before = fingerprint_file(file)

    file.write_bytes(b"BBBB")
    after = fingerprint_file(file)

    assert before is not None
    assert after is not None
    assert before.bytes_read == after.bytes_read == 4
    assert before.digest != after.digest


def test_fingerprint_is_stable_for_identical_content(tmp_path: Path) -> None:
    first = tmp_path / "first.bin"
    second = tmp_path / "second.bin"
    first.write_bytes(b"same content")
    second.write_bytes(b"same content")

    assert fingerprint_file(first) == fingerprint_file(second)


def test_fingerprint_failure_is_nonfatal(tmp_path: Path) -> None:
    assert fingerprint_file(tmp_path / "missing.bin") is None
