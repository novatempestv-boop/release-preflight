import argparse
from pathlib import Path

from .inventory import inventory_build


def _human_bytes(value: int) -> str:
    amount = float(value)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if amount < 1024 or unit == "TB":
            return f"{amount:.2f} {unit}"
        amount /= 1024
    return f"{value} B"


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="preflight",
        description="Check the build before you ship the build.",
    )
    parser.add_argument("build", type=Path, help="Finished build folder")
    args = parser.parse_args()
    inventory = inventory_build(args.build)

    print("Release Preflight")
    print(f"Files: {len(inventory.files):,}")
    print(f"Size: {_human_bytes(inventory.total_bytes)}")
    status = "Complete" if inventory.coverage_complete else "Limited"
    print(f"Coverage: {status}")


if __name__ == "__main__":
    main()
