from pathlib import Path

from preflight.inventory import inventory_build
from preflight.portability import inspect_paths, inspect_relative_paths


def test_case_only_collision() -> None:
    issues = inspect_relative_paths((Path("Hero.png"), Path("hero.png")))
    assert any(issue.rule_id == "PTH-004" for issue in issues)


def test_windows_reserved_name() -> None:
    issues = inspect_relative_paths((Path("CON.txt"),))
    assert any(issue.rule_id == "PTH-003" for issue in issues)


def test_normal_paths_are_quiet(tmp_path: Path) -> None:
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "hero.png").write_bytes(b"x")
    assert inspect_paths(inventory_build(tmp_path)) == ()
