import os
from pathlib import Path

from .models import FileRecord, Inventory


def inventory_build(root: Path) -> Inventory:
    """Inventory a build read-only, without following directory symlinks."""
    root = root.resolve()
    if not root.is_dir():
        raise ValueError("Build path must be a directory.")

    files: list[FileRecord] = []
    inaccessible: list[Path] = []
    total = 0

    def onerror(error: OSError) -> None:
        filename = getattr(error, "filename", None)
        if filename:
            path = Path(filename)
            try:
                inaccessible.append(path.relative_to(root))
            except ValueError:
                inaccessible.append(path)

    for directory, dirnames, filenames in os.walk(root, topdown=True, followlinks=False, onerror=onerror):
        directory_path = Path(directory)

        # Never descend into symlinked directories. Record them as uninspected so
        # "complete coverage" never quietly means "we skipped something."
        kept_dirs = []
        for name in dirnames:
            path = directory_path / name
            try:
                if path.is_symlink():
                    inaccessible.append(path.relative_to(root))
                else:
                    kept_dirs.append(name)
            except OSError:
                inaccessible.append(path.relative_to(root))
        dirnames[:] = kept_dirs

        for name in filenames:
            path = directory_path / name
            try:
                relative = path.relative_to(root)
                if path.is_symlink():
                    inaccessible.append(relative)
                    continue
                stat = path.stat()
                if not path.is_file():
                    continue
                files.append(FileRecord(relative, stat.st_size, path.suffix.lower()))
                total += stat.st_size
            except OSError:
                try:
                    inaccessible.append(path.relative_to(root))
                except ValueError:
                    inaccessible.append(path)

    return Inventory(
        root,
        tuple(sorted(files, key=lambda item: str(item.relative_path))),
        total,
        tuple(sorted(set(inaccessible), key=str)),
    )
