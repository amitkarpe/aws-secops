"""Small CSV and Markdown action-plan exports for the bounded backlog."""

from __future__ import annotations

import csv
import io
from typing import Iterable


FIELDS = (
    "finding",
    "priority",
    "recommended_fix",
    "owner",
    "approval_required",
    "status",
    "target",
)


def action_plan(findings: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {
            "finding": f"{item['resource_type']}/{item['resource_name']}: {item['control']}",
            "priority": item["severity"],
            "recommended_fix": item["recommendation"],
            "owner": item.get("owner", ""),
            "approval_required": "YES",
            "status": item["status"],
            "target": item.get("target", ""),
        }
        for item in findings
        if item["status"] == "NON_COMPLIANT"
    ]


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
        "# Pilot v1.1 compliance reduction plan",
        "",
        f"Open actions: **{len(rows)}**",
        "",
        "| Finding | Priority | Recommended fix | Owner | Approval required | Status | Target |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    lines.extend(
        "| " + " | ".join(_cell(row[field]) for field in FIELDS) + " |"
        for row in rows
    )
    if not rows:
        lines.append("| No open findings | — | No action required |  | — | COMPLIANT |  |")
    return "\n".join(lines) + "\n"
