"""M3B synthetic grouped/manual selection over the M2 truth and M3A batch adapter."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from .csv_bulk_pilot import PILOT_CONTROL, CsvCandidatePilot
from .scaled_findings import FindingQuery, MAX_PAGE_SIZE, ScaledFindingStore


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")
    ).hexdigest()


class GroupedSelectionPilot(CsvCandidatePilot):
    """Server-owned manual selection; changing a view never changes selection."""

    def __init__(self, store: ScaledFindingStore | None = None) -> None:
        super().__init__(store)
        self._selection: dict[str, dict[str, str]] = {}

    @staticmethod
    def _query(**values: Any) -> FindingQuery:
        query = FindingQuery(**values)
        if query.control_key != PILOT_CONTROL:
            raise ValueError("M3B accepts only the restricted_ssh control filter")
        return query

    def selection_receipt(self, *, include_ids: bool = False) -> dict[str, Any]:
        finding_ids = sorted(self._selection)
        receipt = {
            "version": 1,
            "selected_count": len(finding_ids),
            "selection_digest": _digest(finding_ids),
            "read_only": True,
        }
        if include_ids:
            receipt["finding_ids"] = finding_ids
        return receipt

    def view(
        self,
        *,
        account_alias: str | None = None,
        config_status: str | None = None,
        exception_status: str | None = None,
        sort_by: str = "finding_id",
        sort_direction: str = "asc",
        page: int = 1,
        limit: int = 25,
        group_by: str = "account_alias",
    ) -> dict[str, Any]:
        """Return one bounded Config-style page and aggregate group counts only."""
        query = self._query(
            control_key=PILOT_CONTROL,
            account_alias=account_alias,
            config_status=config_status,
            exception_status=exception_status,
            sort_by=sort_by,
            sort_direction=sort_direction,
            page=page,
            limit=limit,
        )
        page_value = self.store.query(query)
        groups = self.store.grouped_summary(query, group_by)
        return {
            "version": 1,
            "control": PILOT_CONTROL,
            "page": page_value,
            "groups": groups,
            "selection": self.selection_receipt(),
            "model_context": "ONE_BOUNDED_PAGE_AND_GROUP_COUNTS",
            "read_only": True,
        }

    def add(self, finding_id: str) -> dict[str, Any]:
        """Add one explicit current finding ID; hidden rows are never implied."""
        row = self.store.resolve_finding_id(finding_id)
        if row is None:
            raise ValueError("unknown finding ID")
        if row["control_key"] != PILOT_CONTROL:
            raise ValueError("unsupported finding control")
        if row["config_status"] != "NON_COMPLIANT":
            raise ValueError("stale finding cannot be selected")
        self._selection.setdefault(finding_id, row)
        return self.selection_receipt()

    def remove(self, finding_id: str) -> dict[str, Any]:
        if not isinstance(finding_id, str) or finding_id not in self._selection:
            raise ValueError("finding ID is not selected")
        del self._selection[finding_id]
        return self.selection_receipt()

    def select_all_current_filter(
        self,
        *,
        account_alias: str | None = None,
        config_status: str | None = None,
        exception_status: str | None = None,
        sort_by: str = "finding_id",
        sort_direction: str = "asc",
    ) -> dict[str, Any]:
        """Explicitly materialize only the current server-side filtered set."""
        query = self._query(
            control_key=PILOT_CONTROL,
            account_alias=account_alias,
            config_status=config_status,
            exception_status=exception_status,
            sort_by=sort_by,
            sort_direction=sort_direction,
        )
        finding_ids = self.store.matching_finding_ids(query)
        if not finding_ids:
            raise ValueError("current filter has no findings to select")
        for finding_id in finding_ids:
            self.add(finding_id)
        return self.selection_receipt()

    def preview_selection(self) -> dict[str, Any]:
        """Re-resolve selection before freeze, then delegate exact batch behavior to M3A."""
        evidence = self.store.evidence_receipt()
        selected = self.selection_receipt(include_ids=True)
        rows: list[dict[str, str]] = []
        for finding_id in selected["finding_ids"]:
            prior = self._selection[finding_id]
            resolved = self.store.resolve_finding_id(finding_id)
            base = {
                "finding_id": finding_id,
                "account_alias": prior["account_alias"],
                "control_key": prior["control_key"],
                "resource_id": prior["resource_id"],
            }
            if resolved is None:
                rows.append({**base, "preview_state": "UNKNOWN", "reason": "NOT_IN_CURRENT_EVIDENCE"})
            elif resolved["control_key"] != PILOT_CONTROL:
                rows.append({**base, "preview_state": "UNSUPPORTED", "reason": "CONTROL_NOT_IN_M3B"})
            elif resolved["config_status"] != "NON_COMPLIANT":
                rows.append({**base, "preview_state": "STALE", "reason": "CURRENT_EVIDENCE_NOT_NON_COMPLIANT"})
            elif resolved["exception_status"] != "NONE":
                rows.append({**base, "preview_state": "EXCLUDED", "reason": "CURRENT_ONE_TIME_EXCEPTION"})
            else:
                rows.append({**base, "preview_state": "ELIGIBLE", "reason": "CURRENT_EVIDENCE_MATCH"})
        rows.sort(key=lambda row: row["finding_id"])
        eligible = [row for row in rows if row["preview_state"] == "ELIGIBLE"]
        excluded = [row for row in rows if row["preview_state"] == "EXCLUDED"]
        scope = {
            "control": PILOT_CONTROL,
            "eligible": [
                {key: row[key] for key in ("finding_id", "account_alias", "resource_id")}
                for row in eligible
            ],
            "exclusions": [
                {key: row[key] for key in ("finding_id", "account_alias", "resource_id")}
                for row in excluded
            ],
            "selection_digest": selected["selection_digest"],
            "evidence_version": evidence["version"],
            "evidence_digest": evidence["evidence_digest"],
            "selected_accounts": sorted({row["account_alias"] for row in eligible}),
        }
        preview = self._freeze_preview(rows, scope)
        preview["selected_count"] = selected["selected_count"]
        return preview


__all__ = ["GroupedSelectionPilot", "MAX_PAGE_SIZE"]
