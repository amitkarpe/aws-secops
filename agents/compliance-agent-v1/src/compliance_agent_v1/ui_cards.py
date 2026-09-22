"""Deterministic, presentation-only MCP UI cards for Compliance Agent v1."""
from __future__ import annotations

from html import escape
from typing import Any

ALIASES = ("lab-dev", "lab-poc", "lab-qa", "lab-sec")
S3 = "s3-bucket-level-public-access-prohibited"
SSH = "restricted-ssh"

_STATUS = {
    "COMPLIANT": ("✅", "COMPLIANT", "good"),
    "NON_COMPLIANT": ("❌", "NON-COMPLIANT", "bad"),
    "INSUFFICIENT_DATA": ("⏳", "PENDING", "wait"),
    "NOT_REPORTED": ("⛔", "UNAVAILABLE", "muted"),
    "NOT_APPLICABLE": ("🚫", "NOT IN SCOPE", "muted"),
}

_RESIZE_BOOTSTRAP = """<script>
(()=>{const send=()=>{const d=document.documentElement,b=document.body;const natural=Math.max(d.scrollHeight,b?b.scrollHeight:0);const height=Math.min(Math.max(natural+4,260),720);parent.postMessage({type:"ui-size-change",payload:{height}},"*");};new ResizeObserver(send).observe(document.documentElement);addEventListener("load",send,{once:true});requestAnimationFrame(send);})();
</script>"""


def _e(value: object) -> str:
    return escape(str(value), quote=True)


def _badge(status: str, count: int) -> str:
    icon, label, css = _STATUS.get(status, ("⛔", "UNAVAILABLE", "muted"))
    suffix = f" · {count}" if count else ""
    return f'<span class="badge {css}">{icon} {_e(label)}{_e(suffix)}</span>'


def render_fleet_card(evidence: dict[str, Any]) -> str:
    """Render the public-safe four-account matrix; never consumes identifiers."""
    checks = evidence.get("checks")
    if not isinstance(checks, list):
        raise ValueError("fleet UI evidence checks missing")

    matrix: dict[tuple[str, str], tuple[str, int]] = {}
    for item in checks:
        if not isinstance(item, dict):
            raise ValueError("fleet UI evidence row invalid")
        alias = item.get("account_alias")
        control = item.get("control")
        status = item.get("status")
        count = item.get("affected_resources")
        if alias not in ALIASES or control not in {S3, SSH} or not isinstance(status, str) or type(count) is not int:
            raise ValueError("fleet UI evidence row outside contract")
        matrix[(alias, control)] = (status, count)

    if len(matrix) != 8:
        raise ValueError("fleet UI requires exact 4x2 matrix")

    compliant = sum(1 for status, _ in matrix.values() if status == "COMPLIANT")
    noncompliant = sum(1 for status, _ in matrix.values() if status == "NON_COMPLIANT")
    affected = sum(count for status, count in matrix.values() if status == "NON_COMPLIANT")
    fetched = evidence.get("fetched_at") or "unknown"

    rows = []
    for alias in ALIASES:
        s3_status, s3_count = matrix[(alias, S3)]
        ssh_status, ssh_count = matrix[(alias, SSH)]
        rows.append(
            "<tr>"
            f"<th>{_e(alias)}</th>"
            f"<td>{_badge(s3_status, s3_count)}</td>"
            f"<td>{_badge(ssh_status, ssh_count)}</td>"
            "</tr>"
        )

    next_action = "Fix S3" if any(matrix[(a, S3)][0] == "NON_COMPLIANT" for a in ALIASES) else (
        "Fix SSH" if any(matrix[(a, SSH)][0] == "NON_COMPLIANT" for a in ALIASES) else "No remediation needed"
    )

    return f"""<!doctype html>
<html><head><meta charset="utf-8"><style>
:root{{color-scheme:light dark;font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}}
*{{box-sizing:border-box}}body{{margin:0;padding:2px;background:transparent;color:CanvasText}}
.card{{border:1px solid color-mix(in srgb,CanvasText 18%,transparent);border-radius:14px;padding:16px;background:Canvas;box-shadow:0 4px 18px rgba(0,0,0,.08)}}
.head{{display:flex;justify-content:space-between;gap:12px;align-items:flex-start;margin-bottom:14px}}
h2{{font-size:16px;margin:0 0 3px}}.sub{{opacity:.68;font-size:11px}}
.metrics{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin:12px 0}}
.metric{{border:1px solid color-mix(in srgb,CanvasText 14%,transparent);border-radius:10px;padding:10px}}
.metric b{{font-size:20px;display:block}}.metric span{{font-size:10px;opacity:.7}}
table{{border-collapse:separate;border-spacing:0;width:100%;font-size:12px;overflow:hidden;border:1px solid color-mix(in srgb,CanvasText 14%,transparent);border-radius:10px}}
th,td{{padding:9px 10px;border-bottom:1px solid color-mix(in srgb,CanvasText 10%,transparent);text-align:left}}
thead th{{font-size:10px;opacity:.72}}tbody tr:last-child th,tbody tr:last-child td{{border-bottom:0}}
.badge{{display:inline-block;border-radius:999px;padding:4px 8px;font-size:10px;font-weight:750;white-space:nowrap}}
.good{{background:#0f7a3c22;color:#2ebd6b}}.bad{{background:#c92a3a22;color:#ff6675}}.wait{{background:#b7791f22;color:#e9a83a}}.muted{{background:#6b728022;opacity:.75}}
.next{{margin-top:12px;border-radius:10px;padding:10px 12px;background:#2563eb18;font-size:11px}}
small{{font-size:9px;opacity:.62}}@media(max-width:650px){{.metrics{{grid-template-columns:1fr}}table{{font-size:11px}}}}
</style></head><body><section class="card">
<div class="head"><div><h2>🛡️ AWS Compliance</h2><div class="sub">4 LAB accounts · 2 controls · 8 checks</div></div><small>{_e(fetched)}</small></div>
<div class="metrics">
<div class="metric"><b>{compliant}/8</b><span>✅ compliant checks</span></div>
<div class="metric"><b>{noncompliant}</b><span>❌ non-compliant checks</span></div>
<div class="metric"><b>{affected}</b><span>⚠️ affected resources</span></div>
</div>
<table><thead><tr><th>AWS Account</th><th>🪣 S3 Block Public Access</th><th>🛡️ Restricted SSH</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>
<div class="next">➡️ Next: <b>{_e(next_action)}</b></div>
</section>{_RESIZE_BOOTSTRAP}</body></html>"""


def render_capability_card(summary: dict[str, Any]) -> str:
    """Render only the fixed public-safe capability fields."""
    controls = summary.get("controls")
    expected = {"s3_ssl", "s3_logging", "s3_backup", "restricted_ssh"}
    if not isinstance(controls, list) or len(controls) != 4:
        raise ValueError("capability UI requires exactly four controls")

    rows = []
    seen = set()
    fields = ("supports_detect", "supports_explain", "supports_prepare", "supports_remediate", "supports_verify")
    for record in controls:
        if not isinstance(record, dict) or record.get("control_key") not in expected:
            raise ValueError("capability UI record is outside the public-safe registry")
        key = record["control_key"]
        if key in seen or record.get("capability_state") not in {"DETECT", "EXPLAIN", "PREPARE", "REMEDIATE", "VERIFY"}:
            raise ValueError("capability UI record is invalid")
        if any(type(record.get(field)) is not bool for field in fields) or type(record.get("requires_human_approval")) is not bool:
            raise ValueError("capability UI support flags are invalid")
        seen.add(key)
        cells = "".join(f"<td>{'✅' if record[field] else '—'}</td>" for field in fields)
        approval = "Required" if record.get("requires_human_approval") else "Not applicable"
        rows.append(
            f"<tr><th>{_e(key)}</th><td><span class=\"badge good\">{_e(record['capability_state'])}</span></td>"
            f"{cells}<td>{_e(approval)}</td></tr>"
        )
    if seen != expected or summary.get("execution_authorized") is not False:
        raise ValueError("capability UI summary is incomplete")

    return f"""<!doctype html>
<html><head><meta charset="utf-8"><style>
:root{{color-scheme:light dark;font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}}
*{{box-sizing:border-box}}body{{margin:0;padding:2px;background:transparent;color:CanvasText}}
.card{{border:1px solid color-mix(in srgb,CanvasText 18%,transparent);border-radius:14px;padding:16px;background:Canvas;box-shadow:0 4px 18px rgba(0,0,0,.08)}}
h2{{font-size:16px;margin:0 0 3px}}.sub{{opacity:.68;font-size:11px;margin-bottom:12px}}
table{{border-collapse:separate;border-spacing:0;width:100%;font-size:11px;overflow:hidden;border:1px solid color-mix(in srgb,CanvasText 14%,transparent);border-radius:10px}}
th,td{{padding:8px;border-bottom:1px solid color-mix(in srgb,CanvasText 10%,transparent);text-align:center}}
th:first-child,td:first-child{{text-align:left}}thead th{{font-size:9px;opacity:.72}}tbody tr:last-child th,tbody tr:last-child td{{border-bottom:0}}
.badge{{display:inline-block;border-radius:999px;padding:4px 8px;font-size:9px;font-weight:750}}.good{{background:#0f7a3c22;color:#2ebd6b}}
.note{{margin-top:12px;font-size:10px;opacity:.72}}@media(max-width:720px){{table{{font-size:9px}}th,td{{padding:6px 4px}}}}
</style></head><body><section class="card">
<h2>🧭 Compliance capabilities</h2><div class="sub">Sanitized metadata · no findings · no execution authorization</div>
<table><thead><tr><th>Control</th><th>State</th><th>Detect</th><th>Explain</th><th>Prepare</th><th>Remediate</th><th>Verify</th><th>Approval</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>
<div class="note">Human approval remains separate from technical support. Existing governed execution controls remain unchanged.</div>
</section>{_RESIZE_BOOTSTRAP}</body></html>"""
