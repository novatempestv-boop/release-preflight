from collections import Counter
from dataclasses import dataclass

from .models import Inventory


@dataclass(frozen=True, slots=True)
class CategoryStat:
    name: str
    files: int
    bytes: int


CATEGORIES = {
    "Audio": {".wav", ".mp3", ".ogg", ".flac", ".aac", ".m4a"},
    "Video": {".mp4", ".webm", ".mov", ".mkv", ".avi"},
    "Images": {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tga"},
    "Executables": {".exe", ".dll", ".so", ".dylib", ".app"},
    "Archives": {".zip", ".7z", ".rar", ".tar", ".gz"},
}


def category_for(extension: str) -> str:
    for name, extensions in CATEGORIES.items():
        if extension in extensions:
            return name
    return "Other"


def composition(inventory: Inventory) -> tuple[CategoryStat, ...]:
    counts: Counter[str] = Counter()
    sizes: Counter[str] = Counter()
    for file in inventory.files:
        category = category_for(file.extension)
        counts[category] += 1
        sizes[category] += file.size
    return tuple(
        CategoryStat(name, counts[name], sizes[name])
        for name in sorted(counts, key=lambda item: sizes[item], reverse=True)
    )


def largest_files(inventory: Inventory, limit: int = 5):
    return tuple(sorted(inventory.files, key=lambda file: file.size, reverse=True)[:limit])


@dataclass(frozen=True, slots=True)
class DuplicateGroup:
    paths: tuple
    bytes_each: int

    @property
    def wasted_bytes(self) -> int:
        return self.bytes_each * (len(self.paths) - 1)


def duplicate_groups(inventory: Inventory, minimum_size: int = 1024 * 1024) -> tuple[DuplicateGroup, ...]:
    """Find exact duplicate files without hashing the whole build."""
    import hashlib

    by_size = {}
    for file in inventory.files:
        if file.size >= minimum_size:
            by_size.setdefault(file.size, []).append(file)

    groups = []
    for size, candidates in by_size.items():
        if len(candidates) < 2:
            continue

        by_digest = {}
        for file in candidates:
            digest = hashlib.sha256()
            try:
                with (inventory.root / file.relative_path).open("rb") as handle:
                    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                        digest.update(chunk)
            except OSError:
                continue
            by_digest.setdefault(digest.digest(), []).append(file.relative_path)

        for paths in by_digest.values():
            if len(paths) > 1:
                groups.append(DuplicateGroup(tuple(sorted(paths, key=str)), size))

    return tuple(sorted(groups, key=lambda g: g.wasted_bytes, reverse=True))
