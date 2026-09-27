from pathlib import Path

from preflight.inventory import inventory_build
from preflight.secrets import inspect_secret_contents


def test_credential_value_is_never_returned(tmp_path: Path) -> None:
    secret = "super-secret-value-12345"
    (tmp_path / "config.json").write_text(f'{{"api_key": "{secret}"}}')

    findings = inspect_secret_contents(inventory_build(tmp_path))

    assert len(findings) == 1
    assert findings[0].rule_id == "SEC-102"
    assert findings[0].line == 1
    assert secret not in repr(findings[0])


def test_private_key_header_is_detected(tmp_path: Path) -> None:
    (tmp_path / "config.txt").write_text("-----BEGIN PRIVATE KEY-----\nfake")
    findings = inspect_secret_contents(inventory_build(tmp_path))
    assert findings[0].rule_id == "SEC-101"
    assert findings[0].confidence == "Certain"


def test_ordinary_config_is_quiet(tmp_path: Path) -> None:
    (tmp_path / "config.json").write_text('{"volume": 0.8, "fullscreen": true}')
    assert inspect_secret_contents(inventory_build(tmp_path)) == ()
