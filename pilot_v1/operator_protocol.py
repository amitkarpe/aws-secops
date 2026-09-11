"""Small one-use confirmation gate for intentional demo reset operations."""
from __future__ import annotations

import secrets
import threading
import time


class ConfirmationGate:
    def __init__(self, ttl_seconds: int = 120):
        if not 30 <= ttl_seconds <= 600:
            raise ValueError("confirmation TTL out of bounds")
        self.ttl_seconds = ttl_seconds
        self.lock = threading.Lock()
        self.tokens: dict[str, tuple[str, str, float]] = {}

    def issue(self, family: str, fingerprint: str) -> str:
        if family not in {"s3", "sg"} or not isinstance(fingerprint, str) or len(fingerprint) != 64:
            raise ValueError("invalid confirmation scope")
        token = secrets.token_urlsafe(24)
        now = time.monotonic()
        with self.lock:
            # Keep only live tokens for the other family. A new confirmation
            # invalidates any older confirmation for the same family.
            self.tokens = {k: v for k, v in self.tokens.items() if v[2] > now and v[0] != family}
            self.tokens[token] = (family, fingerprint, now + self.ttl_seconds)
        return token

    def consume(self, token: str, family: str, fingerprint: str) -> None:
        if not isinstance(token, str) or len(token) > 128:
            raise ValueError("invalid confirmation token")
        now = time.monotonic()
        with self.lock:
            value = self.tokens.pop(token, None)
        if not value or value[2] <= now or value[:2] != (family, fingerprint):
            raise ValueError("stale or mismatched confirmation")
