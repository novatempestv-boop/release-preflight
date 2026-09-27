from pathlib import Path

from preflight.inventory import inventory_build
from preflight.portability import inspect_paths


def test_case_only_collision(tmp_path: Path) -> None:
    (tmp_path / "Hero.png").write_bytes(b"a")
    (tmp_path / "hero.png").write_bytes(b"b")
    issues = inspect_paths(inventory_build(tmp_path))
    assert any(issue.rule_id == "PTH-004" for issue in issues)


def test_windows_reserved_name(tmp_path: Path) -> None:
    (tmp_path / "CON.txt").write_text("x")
    issues = inspect_paths(inventory_build(tmp_path))
    assert any(issue.rule_id == "PTH-003" for issue in issues)


def test_normal_paths_are_quiet(tmp_path: Path) -> None:
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "hero.png").write_bytes(b"x")
    assert inspect_paths(inventory_build(tmp_path)) == ()
