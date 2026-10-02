from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .models import Inventory


@dataclass(frozen=True, slots=True)
class PathIssue:
    rule_id: str
    severity: str
    confidence: str
    title: str
    path: Path
    reason: str


WINDOWS_RESERVED = {
    "con", "prn", "aux", "nul",
    *(f"com{i}" for i in range(1, 10)),
    *(f"lpt{i}" for i in range(1, 10)),
}


def inspect_relative_paths(paths: Iterable[Path]) -> tuple[PathIssue, ...]:
    """Inspect logical relative paths without requiring the host filesystem to represent them."""
    issues: list[PathIssue] = []
    casefolded: dict[str, list[Path]] = {}

    for path in paths:
        text = str(path).replace("\\", "/")
        casefolded.setdefault(text.casefold(), []).append(path)

        if len(text) > 240:
            issues.append(PathIssue(
                "PTH-001", "Warning", "High", "Very long path", path,
                f"The relative path is {len(text)} characters long and may cause portability or tooling problems.",
            ))

        for part in path.parts:
            if part.endswith((" ", ".")):
                issues.append(PathIssue(
                    "PTH-002", "Warning", "Certain", "Trailing space or dot", path,
                    "A path component ends in a space or dot, which is problematic on Windows.",
                ))
                break

            stem = part.split(".", 1)[0].casefold()
            if stem in WINDOWS_RESERVED:
                issues.append(PathIssue(
                    "PTH-003", "Warning", "Certain", "Windows-reserved name", path,
                    f'"{part}" uses a filename reserved by Windows.',
                ))
                break

    for collision_paths in casefolded.values():
        if len(collision_paths) > 1:
            ordered = sorted(collision_paths, key=str)
            shown = ", ".join(str(path) for path in ordered)
            issues.append(PathIssue(
                "PTH-004", "Warning", "Certain", "Case-only path collision",
                ordered[0],
                f"These paths differ only by letter case: {shown}. This can break across filesystems.",
            ))

    return tuple(sorted(issues, key=lambda issue: (issue.rule_id, str(issue.path))))


def inspect_paths(inventory: Inventory) -> tuple[PathIssue, ...]:
    return inspect_relative_paths(file.relative_path for file in inventory.files)
