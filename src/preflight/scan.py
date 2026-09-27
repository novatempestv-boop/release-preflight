from dataclasses import dataclass

from .analysis import CategoryStat, DuplicateGroup, composition, duplicate_groups, largest_files
from .detection import Detection, detect
from .inventory import inventory_build
from .models import FileRecord, Inventory
from .portability import PathIssue, inspect_paths
from .rules import Finding, inspect
from .secrets import SecretFinding, inspect_secret_contents


@dataclass(frozen=True, slots=True)
class ScanResult:
    inventory: Inventory
    findings: tuple[Finding, ...]
    path_issues: tuple[PathIssue, ...]
    secret_findings: tuple[SecretFinding, ...]
    detections: tuple[Detection, ...]
    composition: tuple[CategoryStat, ...]
    largest_files: tuple[FileRecord, ...]
    duplicates: tuple[DuplicateGroup, ...]

    @property
    def coverage_complete(self) -> bool:
        return self.inventory.coverage_complete


def scan_build(root) -> ScanResult:
    inventory = inventory_build(root)
    return ScanResult(
        inventory=inventory,
        findings=inspect(inventory),
        path_issues=inspect_paths(inventory),
        secret_findings=inspect_secret_contents(inventory),
        detections=detect(inventory),
        composition=composition(inventory),
        largest_files=largest_files(inventory),
        duplicates=duplicate_groups(inventory),
    )
