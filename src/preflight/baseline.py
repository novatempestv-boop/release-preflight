import json
from dataclasses import dataclass
from pathlib import Path

from .fingerprint import fingerprint_file
from .models import Inventory

BASELINE_SCHEMA_VERSION = 2


@dataclass(frozen=True, slots=True)
class SnapshotEntry:
    path: str
    size: int
    fingerprint: str | None = None


@dataclass(frozen=True, slots=True)
class BuildSnapshot:
    files: tuple[SnapshotEntry, ...]
    total_bytes: int


@dataclass(frozen=True, slots=True)
class BuildDiff:
    added: tuple[SnapshotEntry, ...]
    removed: tuple[SnapshotEntry, ...]
    size_changed: tuple[tuple[SnapshotEntry, SnapshotEntry], ...]
    content_changed: tuple[tuple[SnapshotEntry, SnapshotEntry], ...]
    content_unverified: tuple[SnapshotEntry, ...]
    unchanged: int
    bytes_delta: int
    growth_by_top_level: tuple[tuple[str, int], ...] = ()


def snapshot_inventory(inventory: Inventory, *, include_fingerprints: bool = False) -> BuildSnapshot:
    """Create a portable snapshot; content hashing is opt-in because it reads file bytes."""
    entries: list[SnapshotEntry] = []
    for file in inventory.files:
        fingerprint = None
        if include_fingerprints:
            result = fingerprint_file(inventory.root / file.relative_path)
            fingerprint = result.digest if result is not None else None
        entries.append(SnapshotEntry(file.relative_path.as_posix(), file.size, fingerprint))
    return BuildSnapshot(tuple(entries), inventory.total_bytes)


def baseline_data(snapshot: BuildSnapshot) -> dict:
    return {
        "schema_version": BASELINE_SCHEMA_VERSION,
        "total_bytes": snapshot.total_bytes,
        "files": [
            {
                "path": entry.path,
                "size": entry.size,
                **({"fingerprint": entry.fingerprint} if entry.fingerprint is not None else {}),
            }
            for entry in snapshot.files
        ],
    }


def save_baseline(snapshot: BuildSnapshot, path: Path) -> None:
    """Save portable metadata and optional content fingerprints; never build contents."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(baseline_data(snapshot), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def load_baseline(path: Path) -> BuildSnapshot:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") not in (1, BASELINE_SCHEMA_VERSION):
        raise ValueError("Unsupported baseline schema version.")

    files = tuple(
        SnapshotEntry(
            str(item["path"]),
            int(item["size"]),
            str(item["fingerprint"]) if item.get("fingerprint") else None,
        )
        for item in data["files"]
    )
    return BuildSnapshot(files=files, total_bytes=int(data["total_bytes"]))


def _bucket(path: str) -> str:
    return path.split("/", 1)[0] if "/" in path else "(root)"


def diff_snapshots(
    previous: BuildSnapshot,
    current: BuildSnapshot,
    *,
    verify_content: bool = False,
) -> BuildDiff:
    old = {entry.path: entry for entry in previous.files}
    new = {entry.path: entry for entry in current.files}

    added = tuple(new[path] for path in sorted(new.keys() - old.keys()))
    removed = tuple(old[path] for path in sorted(old.keys() - new.keys()))
    changed = tuple(
        (old[path], new[path])
        for path in sorted(old.keys() & new.keys())
        if old[path].size != new[path].size
    )

    content_changed: list[tuple[SnapshotEntry, SnapshotEntry]] = []
    content_unverified: list[SnapshotEntry] = []
    unchanged = 0

    for path in sorted(old.keys() & new.keys()):
        old_entry, new_entry = old[path], new[path]
        if old_entry.size != new_entry.size:
            continue
        if verify_content:
            if old_entry.fingerprint is None:
                content_unverified.append(new_entry)
            else:
                # The caller supplies the current snapshot with fingerprints.
                if new_entry.fingerprint is None:
                    content_unverified.append(new_entry)
                elif old_entry.fingerprint != new_entry.fingerprint:
                    content_changed.append((old_entry, new_entry))
                else:
                    unchanged += 1
        else:
            unchanged += 1

    growth: dict[str, int] = {}
    for entry in added:
        growth[_bucket(entry.path)] = growth.get(_bucket(entry.path), 0) + entry.size
    for entry in removed:
        growth[_bucket(entry.path)] = growth.get(_bucket(entry.path), 0) - entry.size
    for old_entry, new_entry in changed:
        name = _bucket(new_entry.path)
        growth[name] = growth.get(name, 0) + (new_entry.size - old_entry.size)

    growth_by_top_level = tuple(
        sorted(
            ((name, delta) for name, delta in growth.items() if delta),
            key=lambda item: (-abs(item[1]), item[0]),
        )
    )

    return BuildDiff(
        added=added,
        removed=removed,
        size_changed=changed,
        content_changed=tuple(content_changed),
        content_unverified=tuple(content_unverified),
        unchanged=unchanged,
        bytes_delta=current.total_bytes - previous.total_bytes,
        growth_by_top_level=growth_by_top_level,
    )
