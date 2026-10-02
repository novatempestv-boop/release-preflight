from dataclasses import dataclass
from pathlib import Path

from .models import Inventory


@dataclass(frozen=True, slots=True)
class SnapshotEntry:
    path: str
    size: int


@dataclass(frozen=True, slots=True)
class BuildSnapshot:
    files: tuple[SnapshotEntry, ...]
    total_bytes: int


@dataclass(frozen=True, slots=True)
class BuildDiff:
    added: tuple[SnapshotEntry, ...]
    removed: tuple[SnapshotEntry, ...]
    size_changed: tuple[tuple[SnapshotEntry, SnapshotEntry], ...]
    unchanged: int
    bytes_delta: int


def snapshot_inventory(inventory: Inventory) -> BuildSnapshot:
    """Create a cheap metadata snapshot without hashing build contents."""
    entries = tuple(
        SnapshotEntry(file.relative_path.as_posix(), file.size)
        for file in inventory.files
    )
    return BuildSnapshot(entries, inventory.total_bytes)


def diff_snapshots(previous: BuildSnapshot, current: BuildSnapshot) -> BuildDiff:
    old = {entry.path: entry for entry in previous.files}
    new = {entry.path: entry for entry in current.files}

    added = tuple(new[path] for path in sorted(new.keys() - old.keys()))
    removed = tuple(old[path] for path in sorted(old.keys() - new.keys()))
    changed = tuple(
        (old[path], new[path])
        for path in sorted(old.keys() & new.keys())
        if old[path].size != new[path].size
    )
    unchanged = sum(
        1
        for path in old.keys() & new.keys()
        if old[path].size == new[path].size
    )

    return BuildDiff(
        added=added,
        removed=removed,
        size_changed=changed,
        unchanged=unchanged,
        bytes_delta=current.total_bytes - previous.total_bytes,
    )
