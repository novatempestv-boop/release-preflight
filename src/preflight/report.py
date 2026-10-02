import json
from collections import Counter

from .scan import ScanResult

REPORT_SCHEMA_VERSION = 1


def _portable_path(path) -> str:
    """Serialize relative paths consistently across operating systems."""
    return path.as_posix()


def report_data(result: ScanResult) -> dict:
    counts = Counter(item.severity for item in result.findings)
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "summary": {
            "files": len(result.inventory.files),
            "bytes": result.inventory.total_bytes,
            "coverage": "complete" if result.coverage_complete else "limited",
            "uninspected": [_portable_path(path) for path in result.inventory.inaccessible],
            "findings": {name: counts[name] for name in ("Critical", "Warning", "Info")},
            "path_issues": len(result.path_issues),
            "content_secrets": len(result.secret_findings),
        },
        "detections": [
            {"kind": x.kind, "name": x.name, "confidence": x.confidence, "evidence": list(x.evidence)}
            for x in result.detections
        ],
        "composition": [
            {"name": x.name, "files": x.files, "bytes": x.bytes}
            for x in result.composition
        ],
        "largest_files": [
            {"path": _portable_path(x.relative_path), "bytes": x.size}
            for x in result.largest_files
        ],
        "duplicates": [
            {"paths": [_portable_path(path) for path in x.paths], "bytes_each": x.bytes_each, "wasted_bytes": x.wasted_bytes}
            for x in result.duplicates
        ],
        "content_secret_findings": [
            {
                "rule_id": x.rule_id, "severity": x.severity, "confidence": x.confidence,
                "title": x.title, "path": _portable_path(x.path), "line": x.line, "reason": x.reason,
            }
            for x in result.secret_findings
        ],
        "path_findings": [
            {
                "rule_id": x.rule_id, "severity": x.severity, "confidence": x.confidence,
                "title": x.title, "path": _portable_path(x.path), "reason": x.reason,
            }
            for x in result.path_issues
        ],
        "findings": [
            {
                "rule_id": x.rule_id, "severity": x.severity, "confidence": x.confidence,
                "title": x.title, "path": _portable_path(x.path), "reason": x.reason,
                "suggested_action": x.suggested_action,
            }
            for x in result.findings
        ],
    }


def report_json(result: ScanResult) -> str:
    return json.dumps(report_data(result), indent=2, sort_keys=True) + "\n"
