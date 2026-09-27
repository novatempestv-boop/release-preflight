from dataclasses import dataclass
from pathlib import Path

from .models import Inventory


@dataclass(frozen=True, slots=True)
class Finding:
    rule_id: str
    severity: str
    confidence: str
    title: str
    path: Path
    reason: str
    suggested_action: str


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
            findings.append(Finding(
                "SEC-001", "Critical", "High", "Possible sensitive file",
                file.relative_path,
                "This file type is commonly kept out of public release artifacts.",
                "Verify that this file is required. If not, remove it from the release pipeline.",
            ))
        elif name in JUNK_NAMES:
            findings.append(Finding(
                "JNK-001", "Info", "Certain", "Operating-system junk",
                file.relative_path,
                "This file is usually unnecessary in a shipped build.",
                "Exclude it from future release artifacts if it is not required.",
            ))
        elif suffix in DEBUG_SUFFIXES:
            findings.append(Finding(
                "DBG-001", "Warning", "High", "Debug or diagnostic leftover",
                file.relative_path,
                "Logs and dumps are worth reviewing before distribution.",
                "Confirm that this diagnostic file belongs in the public build.",
            ))
        elif suffix in SOURCE_SUFFIXES:
            findings.append(Finding(
                "SRC-001", "Warning", "High", "Source artwork in build",
                file.relative_path,
                "Editable source assets are unusual in a finished build.",
                "Confirm that players need this source asset; otherwise exclude it from packaging.",
            ))

        # Percentage alone is deliberately not enough: tiny builds should not scream
        # about tiny files merely because one happens to dominate the artifact.
        if file.size >= 100 * 1024 * 1024:
            share = file.size / inventory.total_bytes if inventory.total_bytes else 0
            reason = f"This file is {file.size / (1024 * 1024):.1f} MB"
            if share >= 0.10:
                reason += f" and accounts for {share:.1%} of the build"
            reason += "."
            findings.append(Finding(
                "SIZ-001", "Info", "Certain", "Large file",
                file.relative_path, reason,
                "Review whether this file's size is expected for the release.",
            ))

    order = {"Critical": 0, "Warning": 1, "Info": 2}
    return tuple(sorted(findings, key=lambda f: (order[f.severity], str(f.path), f.rule_id)))
