import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ContentFingerprint:
    algorithm: str
    digest: str
    bytes_read: int


def fingerprint_file(path: Path, chunk_size: int = 1024 * 1024) -> ContentFingerprint | None:
    """Hash one file by streaming it; an unreadable file never fails the scan."""
    digest = hashlib.sha256()
    bytes_read = 0
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(chunk_size), b""):
                digest.update(chunk)
                bytes_read += len(chunk)
    except OSError:
        return None

    return ContentFingerprint(
        algorithm="sha256",
        digest=digest.hexdigest(),
        bytes_read=bytes_read,
    )
