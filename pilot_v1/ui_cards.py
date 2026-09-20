"""Deterministic native MCP UI cards for the governed Compliance Agent shell."""
from __future__ import annotations

import json
from html import escape
from typing import Any

from mcp.types import CallToolResult, EmbeddedResource, TextContent, TextResourceContents

S3_CONTROL = "s3-bucket-level-public-access-prohibited"
SG_CONTROL = "restricted-ssh"

_CONTROL_LABELS = {
    S3_CONTROL: "🪣 S3 Block Public Access",
    SG_CONTROL: "🛡️ Restricted SSH",
}


def _e(value: object) -> str:
    return escape(str(value), quote=True)


def _list(value: object) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
        return []
    return value


def _pill(text: str, css: str) -> str:
    return f'<span class="pill {css}">{_e(text)}</span>'


def _shell(title: str, subtitle: str, body: str, details: str = "") -> str:
    detail_html = (
        f'<details><summary>⚙️ Technical details</summary><div class="technical">{details}</div></details>'
        if details else ""
    )
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><style>
:root{{color-scheme:light dark;font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}}
*{{box-sizing:border-box}}body{{margin:0;padding:2px;background:transparent;color:CanvasText}}
.card{{border:1px solid color-mix(in srgb,CanvasText 18%,transparent);border-radius:14px;padding:16px;background:Canvas;box-shadow:0 4px 18px rgba(0,0,0,.08)}}
h2{{font-size:16px;margin:0 0 3px}}.sub{{font-size:11px;opacity:.68;margin-bottom:13px}}
.grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin:10px 0 12px}}
.metric{{border:1px solid color-mix(in srgb,CanvasText 14%,transparent);border-radius:10px;padding:10px}}
.metric b{{display:block;font-size:19px}}.metric span{{font-size:10px;opacity:.7}}
.line{{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:8px 0;font-size:11px}}
.label{{min-width:126px;opacity:.68}}.pill{{border-radius:999px;padding:4px 8px;font-size:10px;font-weight:750}}
.good{{background:#0f7a3c22;color:#2ebd6b}}.bad{{background:#c92a3a22;color:#ff6675}}.wait{{background:#b7791f22;color:#e9a83a}}.info{{background:#2563eb22;color:#6ea8ff}}.muted{{background:#6b728022;opacity:.78}}
.callout{{border-radius:10px;padding:10px 12px;margin-top:11px;font-size:11px;background:#2563eb18}}
.warning{{background:#b7791f18}}table{{border-collapse:separate;border-spacing:0;width:100%;font-size:11px;border:1px solid color-mix(in srgb,CanvasText 14%,transparent);border-radius:10px;overflow:hidden;margin-top:10px}}
th,td{{padding:8px 9px;text-align:left;border-bottom:1px solid color-mix(in srgb,CanvasText 10%,transparent)}}tr:last-child th,tr:last-child td{{border-bottom:0}}
details{{margin-top:12px;border-top:1px solid color-mix(in srgb,CanvasText 12%,transparent);padding-top:10px;font-size:10px}}
summary{{cursor:pointer;opacity:.7}}.technical{{margin-top:8px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;overflow-wrap:anywhere;opacity:.82}}
code{{font-family:inherit}}@media(max-width:650px){{.grid{{grid-template-columns:1fr}}.label{{min-width:auto}}}}
</style></head><body><section class="card">
<h2>{_e(title)}</h2><div class="sub">{_e(subtitle)}</div>
{body}{detail_html}
</section></body></html>"""


def _technical(value: dict[str, Any]) -> str:
    bits = []
    for key, label in (("batch_id", "Batch ID"), ("scope_hash", "Scope hash"), ("decision", "Decision")):
        item = value.get(key)
        if item not in (None, ""):
            bits.append(f"<div><b>{_e(label)}:</b> <code>{_e(item)}</code></div>")
    return "".join(bits)


def render_remediation_preview(value: dict[str, Any]) -> str:
    control = value.get("control")
    selected = _list(value.get("selected_accounts"))
    unselected = _list(value.get("unselected_accounts"))
    included = _list(value.get("pending_aliases"))
    excluded = _list(value.get("excluded_aliases"))
    excluded_resources = _list(value.get("excluded_resources"))
    action = (
        "Bring bucket-level Block Public Access into the compliant configuration."
        if control == S3_CONTROL
        else "Remove unrestricted SSH ingress from the selected demo Security Groups."
    )
    exception = value.get("exception") if isinstance(value.get("exception"), dict) else {}
    reason = exception.get("reason") if isinstance(exception, dict) else None

    body = (
        '<div class="grid">'
        f'<div class="metric"><b>{len(selected)}</b><span>🎯 selected accounts</span></div>'
        f'<div class="metric"><b>{len(included)}</b><span>✅ included findings</span></div>'
        f'<div class="metric"><b>{len(excluded)}</b><span>⏭ excluded findings</span></div>'
        '</div>'
        f'<div class="line"><span class="label">Selected</span>{_pill(", ".join(selected) or "None", "info")}</div>'
        f'<div class="line"><span class="label">Outside scope</span>{_pill(", ".join(unselected) or "None", "muted")}</div>'
        f'<div class="line"><span class="label">Exact action</span><span>{_e(action)}</span></div>'
    )
    if excluded_resources:
        body += (
            f'<div class="line"><span class="label">Excluded</span>{_pill(", ".join(excluded_resources), "wait")}</div>'
            + (f'<div class="line"><span class="label">Reason</span><span>{_e(reason)}</span></div>' if reason else "")
        )
    body += (
        '<div class="callout warning"><b>✋ Human approval required</b><br>'
        'Approve + Submit applies only this frozen scope. Reject + Submit performs zero remediation writes.</div>'
    )
    return _shell(
        "Remediation ready",
        _CONTROL_LABELS.get(control, str(control)),
        body,
        _technical(value),
    )


def render_execution_result(value: dict[str, Any]) -> str:
    control = value.get("control")
    selected = _list(value.get("selected_accounts"))
    excluded = _list(value.get("excluded_aliases"))
    changed = value.get("mutation_count")
    if type(changed) is not int:
        changed = len(_list(value.get("included_aliases")))
    service = str(value.get("aws_service_verification") or ("VERIFIED" if value.get("provider_verified") is True else "PENDING"))
    config = value.get("aws_config_evaluation", "PENDING")
    config_label = "PENDING" if isinstance(config, dict) else str(config)
    applied = bool(value.get("aws_change_applied", value.get("decision") in {"APPROVE", "APPLIED_PENDING_VERIFICATION", "RECOVERED_VERIFIED"}))

    body = (
        '<div class="grid">'
        f'<div class="metric"><b>{len(selected)}</b><span>🎯 selected accounts</span></div>'
        f'<div class="metric"><b>{_e(changed)}</b><span>✅ changes applied</span></div>'
        f'<div class="metric"><b>{len(excluded)}</b><span>⏭ excluded</span></div>'
        '</div>'
        f'<div class="line"><span class="label">AWS change</span>{_pill("✅ Applied" if applied else "⛔ Not applied", "good" if applied else "bad")}</div>'
        f'<div class="line"><span class="label">AWS service verification</span>{_pill("✅ Verified" if service == "VERIFIED" else "⏳ " + service.replace("_"," ").title(), "good" if service == "VERIFIED" else "wait")}</div>'
        f'<div class="line"><span class="label">AWS Config evaluation</span>{_pill("⏳ " + config_label.replace("_"," ").title(), "wait" if config_label != "COMPLIANT" else "good")}</div>'
        '<div class="callout">➡️ Next: <b>Verify latest</b> for direct AWS state and current Config evaluation.</div>'
    )
    return _shell(
        "✅ AWS change applied" if applied else "Remediation result",
        _CONTROL_LABELS.get(control, str(control)),
        body,
        _technical(value),
    )


def render_verification_result(value: dict[str, Any]) -> str:
    control = value.get("control")
    selected = _list(value.get("selected_accounts"))
    service = str(value.get("aws_service_verification") or "NOT_VERIFIED")
    config = value.get("aws_config_evaluation")
    config_map = config if isinstance(config, dict) else {}

    rows = []
    for alias in selected:
        status = str(config_map.get(alias, "PENDING"))
        css = "good" if status == "COMPLIANT" else "bad" if status == "NON_COMPLIANT" else "wait"
        icon = "✅" if status == "COMPLIANT" else "❌" if status == "NON_COMPLIANT" else "⏳"
        rows.append(f"<tr><th>{_e(alias)}</th><td>{_pill(icon + ' ' + status.replace('_',' '), css)}</td></tr>")

    all_config = bool(selected) and all(config_map.get(alias) == "COMPLIANT" for alias in selected)
    body = (
        f'<div class="line"><span class="label">AWS service verification</span>{_pill("✅ VERIFIED" if service == "VERIFIED" else "❌ " + service.replace("_"," "), "good" if service == "VERIFIED" else "bad")}</div>'
        '<table><tr><th>AWS Account</th><th>AWS Config evaluation</th></tr>'
        + "".join(rows) + "</table>"
        + (
            '<div class="callout">✅ Direct AWS state and AWS Config now agree for the selected scope.</div>'
            if service == "VERIFIED" and all_config
            else '<div class="callout">⏳ AWS Config is asynchronous and may update after direct AWS verification.</div>'
        )
    )
    return _shell(
        "Verification",
        _CONTROL_LABELS.get(control, str(control)),
        body,
        _technical(value),
    )


def tool_result(value: dict[str, Any], *, uri: str, html: str) -> CallToolResult:
    """Preserve exact machine JSON for the model and add one deterministic UI resource."""
    return CallToolResult(
        content=[
            TextContent(type="text", text=json.dumps(value, separators=(",", ":"), sort_keys=True)),
            EmbeddedResource(
                type="resource",
                resource=TextResourceContents(uri=uri, mimeType="text/html", text=html),
            ),
        ],
        structuredContent=value,
    )
