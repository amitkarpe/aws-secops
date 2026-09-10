"""Deterministic management backlog over the common finding contract."""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable

from .findings import MAX_FINDINGS, validate_finding
from .routing import enrich_finding


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

    def upsert(
        self, findings: Iterable[dict[str, Any]], *, evidence_origin: str = "IMPORTED"
    ) -> None:
        if evidence_origin not in {"IMPORTED", "AWS_PROVIDER"}:
            raise ValueError("evidence origin is unsupported")
        for raw in findings:
            finding = validate_finding(raw)
            finding["evidence_origin"] = evidence_origin
            key = _key(finding)
            if key not in self._findings and len(self._findings) >= MAX_FINDINGS:
                raise ValueError(f"backlog cannot exceed {MAX_FINDINGS} findings")
            self._findings[key] = finding

    def open_findings(self) -> list[dict[str, str]]:
        open_findings = [
            enrich_finding(finding)
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
        return open_findings

    def replace_provider(self, source: str, findings: list[dict[str, Any]], synced_at: str) -> None:
        replacement = {key: value for key, value in self._findings.items() if value["source"] != source}
        for raw in findings:
            finding = validate_finding(raw)
            if finding["source"] != source:
                raise ValueError("provider source mismatch")
            finding.update(evidence_origin="AWS_PROVIDER", synced_at=synced_at)
            replacement[_key(finding)] = finding
        if len(replacement) > MAX_FINDINGS:
            raise ValueError(f"backlog cannot exceed {MAX_FINDINGS} findings")
        self._findings = replacement

    def summary(self) -> dict[str, Any]:
        open_findings = self.open_findings()

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
            "by_specialist": grouped("specialist_route"),
            "by_eligibility": grouped("action_eligibility"),
            "priority_findings": open_findings[:10],
            "open_findings": open_findings,
            "recommended_focus": focus,
        }
