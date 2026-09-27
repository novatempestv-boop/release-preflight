import json
from pathlib import Path

from preflight.report import report_json
from preflight.scan import scan_build


def test_report_is_relative_deterministic_and_redacted(tmp_path: Path) -> None:
    secret = "FAKE_REPORT_SECRET_12345"
    config = tmp_path / "config"
    config.mkdir()
    (config / "release.txt").write_text(f"api_key={secret}")

    result = scan_build(tmp_path)
    first = report_json(result)
    second = report_json(result)
    data = json.loads(first)

    assert first == second
    assert secret not in first
    assert str(tmp_path) not in first
    assert data["schema_version"] == 1
    assert data["content_secret_findings"][0]["path"] == "config/release.txt"
    assert data["content_secret_findings"][0]["line"] == 1
