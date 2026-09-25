import argparse
from collections import Counter
from pathlib import Path

from .analysis import composition, largest_files
from .inventory import inventory_build
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
    counts = Counter(f.severity for f in findings)

    print("Release Preflight")
    print(f"Files: {len(inventory.files):,}")
    print(f"Size: {_human_bytes(inventory.total_bytes)}")
    print(f"Coverage: {'Complete' if inventory.coverage_complete else 'Limited'}")
    print(f"Findings: {counts['Critical']} Critical / {counts['Warning']} Warning / {counts['Info']} Info")

    print("\nBuild composition:")
    for stat in composition(inventory):
        percent = (stat.bytes / inventory.total_bytes * 100) if inventory.total_bytes else 0
        print(f"  {stat.name}: {_human_bytes(stat.bytes)} ({percent:.1f}%) · {stat.files} files")

    print("\nLargest files:")
    for file in largest_files(inventory):
        print(f"  {_human_bytes(file.size):>10}  {file.relative_path}")

    for finding in findings:
        print(f"\n[{finding.severity}] {finding.title}")
        print(f"  {finding.path}")
        print(f"  {finding.reason}")
        print(f"  Rule: {finding.rule_id}")


if __name__ == "__main__":
    main()
