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
