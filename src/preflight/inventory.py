from pathlib import Path

from .models import FileRecord, Inventory


def inventory_build(root: Path) -> Inventory:
    """Inventory a build without modifying it or following file symlinks."""
    root = root.resolve()
    if not root.is_dir():
        raise ValueError("Build path must be a directory.")

    files: list[FileRecord] = []
    inaccessible: list[Path] = []
    total = 0

    for path in root.rglob("*"):
        try:
            if path.is_symlink() or not path.is_file():
                continue
            stat = path.stat()
            relative = path.relative_to(root)
            files.append(FileRecord(relative, stat.st_size, path.suffix.lower()))
            total += stat.st_size
        except OSError:
            try:
                inaccessible.append(path.relative_to(root))
            except ValueError:
                inaccessible.append(path)

    return Inventory(root, tuple(files), total, tuple(inaccessible))
