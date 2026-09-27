from pathlib import Path

from preflight.inventory import inventory_build
from preflight.rules import inspect


def test_basic_rules(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("fake=true")
    (tmp_path / "debug.log").write_text("debug")
    (tmp_path / "art.psd").write_text("fake")
    (tmp_path / ".DS_Store").write_text("fake")

    findings = inspect(inventory_build(tmp_path))
    by_rule = {finding.rule_id: finding for finding in findings}

    assert {"SEC-001", "DBG-001", "SRC-001", "JNK-001"} <= set(by_rule)
    assert by_rule["SEC-001"].severity == "Critical"
    assert by_rule["SEC-001"].confidence == "High"


def test_large_file_requires_real_size(tmp_path: Path) -> None:
    (tmp_path / "tiny.bin").write_bytes(b"x" * 100)
    findings = inspect(inventory_build(tmp_path))
    assert all(f.rule_id != "SIZ-001" for f in findings)


def test_large_file_is_reported(tmp_path: Path) -> None:
    path = tmp_path / "cinematic.bin"
    with path.open("wb") as handle:
        handle.truncate(101 * 1024 * 1024)

    findings = inspect(inventory_build(tmp_path))
    large = next(f for f in findings if f.rule_id == "SIZ-001")
    assert large.severity == "Info"
    assert large.confidence == "Certain"
