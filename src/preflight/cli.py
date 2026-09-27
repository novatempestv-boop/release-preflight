import argparse
from collections import Counter
from pathlib import Path

from .analysis import composition, duplicate_groups, largest_files
from .detection import detect
from .inventory import inventory_build
from .portability import inspect_paths
from .rules import inspect


def _human_bytes(value: int) -> str:
    amount = float(value)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if amount < 1024 or unit == "TB":
            return f"{amount:.2f} {unit}"
        amount /= 1024
    return f"{value} B"


def main() -> None:
    parser = argparse.ArgumentParser(prog="preflight", description="Check the build before you ship the build.")
    parser.add_argument("build", type=Path, help="Finished build folder")
    args = parser.parse_args()

    inventory = inventory_build(args.build)
    findings = inspect(inventory)
    path_issues = inspect_paths(inventory)
    counts = Counter(f.severity for f in findings)

    print("Release Preflight")
    print(f"Files: {len(inventory.files):,}")
    print(f"Size: {_human_bytes(inventory.total_bytes)}")
    print(f"Coverage: {'Complete' if inventory.coverage_complete else 'Limited'}")
    if inventory.inaccessible:
        print(f"Uninspected: {len(inventory.inaccessible)} path(s)")
        for path in inventory.inaccessible[:5]:
            print(f"  {path}")
        if len(inventory.inaccessible) > 5:
            print(f"  ... and {len(inventory.inaccessible) - 5} more")
    print(f"Findings: {counts['Critical']} Critical / {counts['Warning']} Warning / {counts['Info']} Info")
    print(f"Path portability: {len(path_issues)} issue(s)")

    detections = detect(inventory)
    if detections:
        print("\nDetected build:")
        for item in detections:
            evidence = ", ".join(item.evidence)
            print(f"  {item.kind}: {item.name} · {item.confidence} confidence")
            print(f"    Evidence: {evidence}")
    else:
        print("\nDetected build: Unknown (not enough evidence)")

    print("\nBuild composition:")
    for stat in composition(inventory):
        percent = (stat.bytes / inventory.total_bytes * 100) if inventory.total_bytes else 0
        print(f"  {stat.name}: {_human_bytes(stat.bytes)} ({percent:.1f}%) · {stat.files} files")

    print("\nLargest files:")
    for file in largest_files(inventory):
        print(f"  {_human_bytes(file.size):>10}  {file.relative_path}")

    duplicates = duplicate_groups(inventory)
    if duplicates:
        print("\nExact duplicates:")
        for group in duplicates:
            print(f"  {_human_bytes(group.wasted_bytes)} potentially wasted · {len(group.paths)} copies")
            for path in group.paths:
                print(f"    {path}")

    if path_issues:
        print("\nPath portability:")
        for issue in path_issues:
            print(f"  [{issue.severity}] {issue.title}")
            print(f"    {issue.path}")
            print(f"    {issue.reason}")
            print(f"    Confidence: {issue.confidence}")
            print(f"    Rule: {issue.rule_id}")

    for finding in findings:
        print(f"\n[{finding.severity}] {finding.title}")
        print(f"  {finding.path}")
        print(f"  {finding.reason}")
        print(f"  Confidence: {finding.confidence}")
        print(f"  Suggested action: {finding.suggested_action}")
        print(f"  Rule: {finding.rule_id}")


if __name__ == "__main__":
    main()
