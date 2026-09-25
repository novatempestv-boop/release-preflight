from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class FileRecord:
    relative_path: Path
    size: int
    extension: str


@dataclass(frozen=True, slots=True)
class Inventory:
    root: Path
    files: tuple[FileRecord, ...]
    total_bytes: int
    inaccessible: tuple[Path, ...]

    @property
    def coverage_complete(self) -> bool:
        return not self.inaccessible
