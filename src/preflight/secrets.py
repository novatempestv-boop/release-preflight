import re
from dataclasses import dataclass
from pathlib import Path

from .models import Inventory


@dataclass(frozen=True, slots=True)
class SecretFinding:
    rule_id: str
    severity: str
    confidence: str
    title: str
    path: Path
    line: int
    reason: str


TEXT_SUFFIXES = {".json", ".toml", ".yaml", ".yml", ".ini", ".cfg", ".conf", ".txt", ".env"}
MAX_FILE_BYTES = 1024 * 1024

PATTERNS = (
    ("SEC-101", "Private key material", "Certain", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("SEC-102", "Credential-like assignment", "Medium", re.compile(
        r"(?i)\b(?:api[_-]?key|access[_-]?token|secret|password|passwd)\b\s*[:=]\s*[\"']?[^\s\"']{8,}"
    )),
)


def inspect_secret_contents(inventory: Inventory) -> tuple[SecretFinding, ...]:
    findings: list[SecretFinding] = []

    for file in inventory.files:
        name = file.relative_path.name.lower()
        if file.size > MAX_FILE_BYTES:
            continue
        if file.extension not in TEXT_SUFFIXES and not name.startswith(".env"):
            continue

        try:
            text = (inventory.root / file.relative_path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for line_number, line in enumerate(text.splitlines(), 1):
            for rule_id, title, confidence, pattern in PATTERNS:
                if pattern.search(line):
                    findings.append(SecretFinding(
                        rule_id, "Critical", confidence, title,
                        file.relative_path, line_number,
                        "Potential sensitive material detected. The matched value is intentionally hidden.",
                    ))
                    break

    return tuple(findings)
