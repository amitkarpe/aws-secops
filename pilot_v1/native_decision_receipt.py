"""Durable, exact native decision receipts for the s3_ssl reject-only tool.

This module has no AWS, CodeBuild, Gateway, Lambda, or executor import. A
receipt is evidence of a native choice; it never grants execution authority.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import threading
import time
import os
from pathlib import Path
from typing import Any

CONTROL = "s3_ssl"
TOOL = "decide_s3_ssl_reject_only_mcp_aws_compliance_planner"
LIVE_EXECUTION_AUTHORIZED = False
_BATCH = re.compile(r"[a-f0-9]{20}\Z")
_SCOPE = re.compile(r"[a-f0-9]{24}\Z")
_IDENTITY = re.compile(r"[A-Za-z0-9_-]{8,128}\Z")
_LOCK = threading.RLock()


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _canonical(value: dict[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


class ReceiptError(ValueError):
    pass


class NativeDecisionReceipts:
    """SQLite transaction boundary; database path is private runtime state."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS frozen (
                    batch_id TEXT PRIMARY KEY, scope_hash TEXT NOT NULL,
                    user_hash TEXT NOT NULL, expires_at INTEGER NOT NULL,
                    state TEXT NOT NULL CHECK(state IN ('PENDING','REJECTED','APPROVE_BLOCKED'))
                );
                CREATE TABLE IF NOT EXISTS receipt (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_id TEXT NOT NULL UNIQUE, scope_hash TEXT NOT NULL,
                    action_hash TEXT NOT NULL, generation_hash TEXT NOT NULL,
                    user_hash TEXT NOT NULL, decision TEXT NOT NULL,
                    outcome TEXT NOT NULL, recorded_at INTEGER NOT NULL,
                    prior_hash TEXT NOT NULL, event_hash TEXT NOT NULL
                );
                CREATE TRIGGER IF NOT EXISTS receipt_no_update BEFORE UPDATE ON receipt
                    BEGIN SELECT RAISE(ABORT, 'receipt is append-only'); END;
                CREATE TRIGGER IF NOT EXISTS receipt_no_delete BEFORE DELETE ON receipt
                    BEGIN SELECT RAISE(ABORT, 'receipt is append-only'); END;
            """)
        os.chmod(self.path, 0o600)
        self.verify()

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        db.execute("PRAGMA synchronous=FULL")
        db.execute("PRAGMA busy_timeout=5000")
        return db

    @staticmethod
    def _validate_binding(tool: str, control: str, batch_id: str, scope_hash: str) -> None:
        if tool != TOOL or control != CONTROL or not isinstance(batch_id, str) or not _BATCH.fullmatch(batch_id) or not isinstance(scope_hash, str) or not _SCOPE.fullmatch(scope_hash):
            raise ReceiptError("unsupported or malformed frozen tool scope")

    def register(self, *, tool: str, control: str, batch_id: str, scope_hash: str,
                 user_id: str, expires_at: int) -> None:
        """Called by a trusted prepare/ASK adapter, never by model input alone."""
        self._validate_binding(tool, control, batch_id, scope_hash)
        if not isinstance(user_id, str) or not user_id or type(expires_at) is not int or not int(time.time()) < expires_at <= int(time.time()) + 1800:
            raise ReceiptError("invalid authenticated freeze binding or TTL")
        with _LOCK, self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                db.execute("INSERT INTO frozen VALUES (?,?,?,?, 'PENDING')", (batch_id, scope_hash, _hash(user_id), expires_at))
                db.commit()
            except (sqlite3.IntegrityError, sqlite3.OperationalError) as exc:
                db.rollback()
                raise ReceiptError("frozen batch already exists or storage unavailable") from exc

    def record(self, *, tool: str, control: str, batch_id: str, scope_hash: str,
               action_id: str, generation_id: str, user_id: str, decision: str,
               decided_at: int) -> dict[str, Any]:
        self._validate_binding(tool, control, batch_id, scope_hash)
        if decision not in {"reject", "approve"} or not all(isinstance(value, str) and _IDENTITY.fullmatch(value) for value in (action_id, generation_id, user_id)) or type(decided_at) is not int:
            raise ReceiptError("invalid native decision identity")
        outcome = "REJECTED" if decision == "reject" else "APPROVE_BLOCKED"
        now = int(time.time())
        if abs(now - decided_at) > 60:
            raise ReceiptError("stale native decision timestamp")
        with _LOCK, self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                frozen = db.execute("SELECT scope_hash,user_hash,expires_at,state FROM frozen WHERE batch_id=?", (batch_id,)).fetchone()
                if frozen is None or frozen[0] != scope_hash or frozen[1] != _hash(user_id) or frozen[2] < now or frozen[3] != "PENDING":
                    raise ReceiptError("stale, consumed, or mismatched frozen batch")
                prior = db.execute("SELECT event_hash FROM receipt ORDER BY sequence DESC LIMIT 1").fetchone()
                prior_hash = prior[0] if prior else "GENESIS"
                event = {"tool": TOOL, "control": CONTROL, "batch_id": batch_id,
                         "scope_hash": scope_hash, "action_hash": _hash(action_id),
                         "generation_hash": _hash(generation_id), "user_hash": _hash(user_id),
                         "decision": decision, "outcome": outcome, "recorded_at": now,
                         "prior_hash": prior_hash}
                event_hash = _hash(_canonical(event))
                db.execute("INSERT INTO receipt (batch_id,scope_hash,action_hash,generation_hash,user_hash,decision,outcome,recorded_at,prior_hash,event_hash) VALUES (?,?,?,?,?,?,?,?,?,?)",
                           (batch_id, scope_hash, event["action_hash"], event["generation_hash"], event["user_hash"], decision, outcome, now, prior_hash, event_hash))
                db.execute("UPDATE frozen SET state=? WHERE batch_id=? AND state='PENDING'", (outcome, batch_id))
                db.commit()
                return {"version": 1, "outcome": outcome, "event_hash": event_hash,
                        "live_execution_authorized": LIVE_EXECUTION_AUTHORIZED,
                        "downstream_dispatches": 0, "aws_writes": 0}
            except BaseException:
                db.rollback()
                raise

    def timeline(self, batch_id: str) -> list[dict[str, Any]]:
        if not isinstance(batch_id, str) or not _BATCH.fullmatch(batch_id):
            raise ReceiptError("invalid batch")
        with self._connect() as db:
            rows = db.execute("SELECT decision,outcome,event_hash FROM receipt WHERE batch_id=?", (batch_id,)).fetchall()
        return [{"decision": row[0], "outcome": row[1], "event_hash": row[2]} for row in rows]

    def verify(self) -> None:
        """Fail closed on a broken append-only chain after restart/reopen."""
        with self._connect() as db:
            rows = db.execute("SELECT sequence,batch_id,scope_hash,action_hash,generation_hash,user_hash,decision,outcome,recorded_at,prior_hash,event_hash FROM receipt ORDER BY sequence").fetchall()
        previous = "GENESIS"
        for number, row in enumerate(rows, start=1):
            sequence, batch_id, scope_hash, action_hash, generation_hash, user_hash, decision, outcome, recorded_at, prior_hash, event_hash = row
            event = {"tool": TOOL, "control": CONTROL, "batch_id": batch_id,
                     "scope_hash": scope_hash, "action_hash": action_hash,
                     "generation_hash": generation_hash, "user_hash": user_hash,
                     "decision": decision, "outcome": outcome, "recorded_at": recorded_at,
                     "prior_hash": prior_hash}
            if sequence != number or prior_hash != previous or event_hash != _hash(_canonical(event)):
                raise ReceiptError("native decision receipt integrity failure")
            previous = event_hash
