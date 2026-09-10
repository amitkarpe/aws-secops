"""Small CSV and Markdown action-plan exports for the bounded backlog."""

from __future__ import annotations

import csv
import io
from typing import Iterable

from .routing import enrich_finding


FIELDS = (
    "source",
    "specialist_route",
    "action_eligibility",
    "evidence_origin",
    "observed_at",
    "synced_at",
    "finding",
    "priority",
    "recommended_fix",
    "owner",
    "approval_required",
    "status",
    "target",
)


def action_plan(findings: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    for finding in findings:
        item = (
            finding
            if "specialist_route" in finding and "action_eligibility" in finding
            else enrich_finding(finding)
        )
        if item["status"] != "NON_COMPLIANT":
            continue
        rows.append({
            "source": item["source"],
            "specialist_route": item["specialist_route"],
            "action_eligibility": item["action_eligibility"],
            "evidence_origin": item.get("evidence_origin", "IMPORTED"),
            "observed_at": item["observed_at"],
            "synced_at": item.get("synced_at", ""),
            "finding": f"{item['resource_type']}/{item['resource_name']}: {item['control']}",
            "priority": item["severity"],
            "recommended_fix": item["recommendation"],
            "owner": item.get("owner", ""),
            "approval_required": (
                "YES" if item["action_eligibility"] == "REMEDIATION_SUPPORTED" else "NO — PLAN ONLY"
            ),
            "status": item["status"],
            "target": item.get("target", ""),
        })
    return rows


def to_csv(findings: Iterable[dict[str, str]]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(
        {
            key: f"'{value}" if value.startswith(("=", "+", "-", "@")) else value
            for key, value in row.items()
        }
        for row in action_plan(findings)
    )
    return output.getvalue()


def _cell(value: str) -> str:
    return value.replace("|", "\\|")


def to_markdown(findings: Iterable[dict[str, str]]) -> str:
    rows = action_plan(findings)
    lines = [
        "# AWS SecOps Platform Phase 1 action plan",
        "",
        f"Open actions: **{len(rows)}**",
        "",
        "| " + " | ".join(field.replace("_", " ").title() for field in FIELDS) + " |",
        "| " + " | ".join("---" for _ in FIELDS) + " |",
    ]
    lines.extend(
        "| " + " | ".join(_cell(row[field]) for field in FIELDS) + " |"
        for row in rows
    )
    if not rows:
        lines.append("| No open findings |" + " |" * (len(FIELDS) - 1))
    return "\n".join(lines) + "\n"
