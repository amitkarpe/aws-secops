"""Bounded v1 read contract shared by HTTP and the restricted MCP bridge."""

import re

FILTERS = {
    "source": {"AWS EC2", "AWS S3", "AWS Config", "CloudSCAPE", "VAPT"},
    "severity": {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"},
    "planning_status": {"UNPLANNED", "PLANNED"},
}


def identity(value, length=64):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{%d}" % length, value):
        raise ValueError("invalid server-owned ID")
    return value


def page(items, arguments, *, findings=False):
    allowed = {"limit", "offset"} | (set(FILTERS) if findings else set())
    if not isinstance(arguments, dict) or set(arguments) - allowed:
        raise ValueError("unsupported query argument")
    for name in ("limit", "offset"):
        if name in arguments and type(arguments[name]) is not int:
            raise ValueError("pagination must be integer")
    limit, offset = arguments.get("limit", 10), arguments.get("offset", 0)
    if not 1 <= limit <= 20 or not 0 <= offset <= 100:
        raise ValueError("limit must be 1–20; offset 0–100")
    for field in FILTERS:
        if field in arguments:
            if not isinstance(arguments[field], str) or arguments[field] not in FILTERS[field]:
                raise ValueError("unsupported filter value")
            items = [item for item in items if item[field] == arguments[field]]
    return {"version": 1, "items": items[offset:offset + limit], "total": len(items),
            "limit": limit, "offset": offset,
            "next_offset": offset + limit if offset + limit < len(items) else None}
