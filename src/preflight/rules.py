from dataclasses import dataclass
from pathlib import Path

from .models import Inventory


@dataclass(frozen=True, slots=True)
class Finding:
    rule_id: str
    severity: str
    title: str
    path: Path
    reason: str


SENSITIVE_NAMES = {".env", ".env.local", ".env.production"}
PRIVATE_KEY_SUFFIXES = {".pem", ".key", ".p12", ".pfx"}
JUNK_NAMES = {".ds_store", "thumbs.db", "desktop.ini"}
DEBUG_SUFFIXES = {".log", ".dmp"}
SOURCE_SUFFIXES = {".psd", ".blend", ".kra", ".xcf"}


def inspect(inventory: Inventory) -> tuple[Finding, ...]:
    findings: list[Finding] = []
    for file in inventory.files:
        name = file.relative_path.name.lower()
        suffix = file.extension
        if name in SENSITIVE_NAMES or suffix in PRIVATE_KEY_SUFFIXES:
            findings.append(Finding("SEC-001", "Critical", "Possible sensitive file", file.relative_path, "This file type is commonly kept out of public release artifacts."))
        elif name in JUNK_NAMES:
            findings.append(Finding("JNK-001", "Info", "Operating-system junk", file.relative_path, "This file is usually unnecessary in a shipped build."))
        elif suffix in DEBUG_SUFFIXES:
            findings.append(Finding("DBG-001", "Warning", "Debug or diagnostic leftover", file.relative_path, "Logs and dumps are worth reviewing before distribution."))
        elif suffix in SOURCE_SUFFIXES:
            findings.append(Finding("SRC-001", "Warning", "Source artwork in build", file.relative_path, "Editable source assets are unusual in a finished build."))
    return tuple(findings)
