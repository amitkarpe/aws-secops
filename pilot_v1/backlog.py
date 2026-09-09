"""Deterministic management backlog over the common finding contract."""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable

from .findings import MAX_FINDINGS, validate_finding


PRIORITY = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}


def _key(finding: dict[str, str]) -> tuple[str, str, str, str]:
    return (
        finding["source"],
        finding["resource_type"],
        finding["resource_id"],
        finding["control"],
    )


class FindingBacklog:
    def __init__(self, findings: Iterable[dict[str, Any]] = ()) -> None:
        self._findings: dict[tuple[str, str, str, str], dict[str, str]] = {}
        self.upsert(findings)

    def upsert(self, findings: Iterable[dict[str, Any]]) -> None:
        for raw in findings:
            finding = validate_finding(raw)
            self._findings[_key(finding)] = finding
            if len(self._findings) > MAX_FINDINGS:
                raise ValueError(f"backlog cannot exceed {MAX_FINDINGS} findings")

    def summary(self) -> dict[str, Any]:
        open_findings = [
            finding
            for finding in self._findings.values()
            if finding["status"] == "NON_COMPLIANT"
        ]
        open_findings.sort(
            key=lambda item: (
                PRIORITY[item["severity"]],
                item["observed_at"],
                item["resource_name"],
                item["control"],
            )
        )

        def grouped(field: str) -> list[dict[str, Any]]:
            return [
                {"name": name, "count": count}
                for name, count in sorted(Counter(item[field] for item in open_findings).items())
            ]

        if open_findings:
            first = open_findings[0]
            focus = (
                f"{first['severity']}: {first['control']} on {first['resource_name']}. "
                f"{first['recommendation']}"
            )
        else:
            focus = "No open findings in the bounded provider set."
        return {
            "total_findings": len(self._findings),
            "total_open": len(open_findings),
            "high_critical": sum(
                item["severity"] in {"HIGH", "CRITICAL"} for item in open_findings
            ),
            "by_source": grouped("source"),
            "by_resource_type": grouped("resource_type"),
            "priority_findings": open_findings[:10],
            "recommended_focus": focus,
        }
