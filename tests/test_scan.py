from pathlib import Path

from preflight.scan import scan_build


def test_scan_result_collects_analysis(tmp_path: Path) -> None:
    (tmp_path / "game.exe").write_bytes(b"x")
    (tmp_path / ".env").write_text("fake=true")

    result = scan_build(tmp_path)

    assert result.coverage_complete is True
    assert len(result.inventory.files) == 2
    assert any(item.name == "Windows" for item in result.detections)
    assert any(finding.rule_id == "SEC-001" for finding in result.findings)
    assert result.composition
    assert result.largest_files
