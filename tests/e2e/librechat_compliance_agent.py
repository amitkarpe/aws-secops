#!/usr/bin/env python3
"""Authenticated LibreChat API E2E for Compliance Agent v1.

Required environment:
  LIBRECHAT_E2E_BEARER_TOKEN   Short-lived JWT for an authorized LibreChat user.

Optional environment:
  LIBRECHAT_BASE_URL           Defaults to http://127.0.0.1:3333.
  LIBRECHAT_AGENT_ID           Defaults to the retained Compliance Agent v1 id.
  LIBRECHAT_E2E_TIMEOUT        Per-case deadline in seconds; defaults to 240.
  LIBRECHAT_E2E_FORWARDED_FOR  Private trusted-proxy test source when required.
  LIBRECHAT_E2E_CONTROL        s3 (default) or ssh.

The token is never logged. The script never submits an approve decision.
"""

from __future__ import annotations

import base64
import json
import os
import re
import sys
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


AGENT_ID = "agent_o1sSYUyZ6Jal-H9M32NT0"
NO_PARENT = "00000000-0000-0000-0000-000000000000"
EXECUTOR_PREFIX = "execute_multi_account_remediation"
S3_CONTROL = "s3-bucket-level-public-access-prohibited"
SSH_CONTROL = "restricted-ssh"

SCENARIOS = {
    "s3": {
        "control": S3_CONTROL,
        "command": "Fix S3",
        "approval_prefix": "Allow Compliance Agent v1 to apply S3 Block Public Access remediation?",
        "status_marker": S3_CONTROL,
        "label": "S3",
    },
    "ssh": {
        "control": SSH_CONTROL,
        "command": "Fix SSH",
        "approval_prefix": "Allow Compliance Agent v1 to apply restricted SSH remediation?",
        "status_marker": SSH_CONTROL,
        "label": "SSH",
    },
}
CONFIRMATION_RE = re.compile(r"\b(?:type|reply|respond)\s+(?:yes|go|approve)\b", re.I)
FORWARDED_FOR = os.environ.get("LIBRECHAT_E2E_FORWARDED_FOR", "").strip()
BROWSER_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
)


class GateFailure(RuntimeError):
    pass


@dataclass
class StreamCapture:
    status_code: int | None = None
    conversation_id: str | None = None
    events: list[Any] = field(default_factory=list)
    error: str | None = None
    ready: threading.Event = field(default_factory=threading.Event)
    conversation_ready: threading.Event = field(default_factory=threading.Event)
    done: threading.Event = field(default_factory=threading.Event)


def env(name: str, default: str | None = None) -> str:
    value = os.environ.get(name, default)
    if value is None or not value.strip():
        raise GateFailure(f"missing required environment variable: {name}")
    return value.strip()


def decode_user_id(token: str) -> str:
    try:
        segment = token.split(".")[1]
        segment += "=" * (-len(segment) % 4)
        payload = json.loads(base64.urlsafe_b64decode(segment))
    except (IndexError, ValueError, json.JSONDecodeError) as exc:
        raise GateFailure("bearer token is not a decodable JWT") from exc
    user_id = payload.get("id")
    if not isinstance(user_id, str) or not user_id:
        raise GateFailure("bearer JWT does not contain a non-empty id claim")
    return user_id


def find_key_strings(value: Any, keys: set[str]) -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key in keys and isinstance(item, str):
                found.append(item)
            found.extend(find_key_strings(item, keys))
    elif isinstance(value, list):
        for item in value:
            found.extend(find_key_strings(item, keys))
    return found


def event_shapes(events: list[Any]) -> list[list[str] | str]:
    shapes: list[list[str] | str] = []
    for event in events[:12]:
        if isinstance(event, dict):
            shapes.append(sorted(event.keys()))
        else:
            shapes.append(type(event).__name__)
    return shapes


def request_json(
    base_url: str,
    token: str,
    method: str,
    path: str,
    body: dict[str, Any] | None = None,
    timeout: float = 30,
) -> tuple[int, Any]:
    data = None if body is None else json.dumps(body, separators=(",", ":")).encode()
    request = Request(
        base_url + path,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": BROWSER_USER_AGENT,
            "X-LibreChat-Generation-Protocol": "2",
            **({"X-Forwarded-For": FORWARDED_FOR} if FORWARDED_FOR else {}),
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else None
    except HTTPError as exc:
        raw = exc.read().decode(errors="replace")[:800]
        raise GateFailure(f"{method} {path} returned HTTP {exc.code}: {raw}") from exc
    except URLError as exc:
        raise GateFailure(f"{method} {path} failed: {exc.reason}") from exc


def start_chat(
    base_url: str,
    token: str,
    user_id: str,
    agent_id: str,
    text: str,
) -> tuple[str, StreamCapture, threading.Thread]:
    client_request_id = f"issue161-{uuid.uuid4().hex}"
    message_id = str(uuid.uuid4())
    payload = {
        "text": text,
        "sender": "User",
        "isCreatedByUser": True,
        "parentMessageId": NO_PARENT,
        "conversationId": "new",
        "messageId": message_id,
        "clientRequestId": client_request_id,
        "endpoint": "agents",
        "agent_id": agent_id,
        "model": agent_id,
        "error": False,
        "isTemporary": False,
    }
    capture = StreamCapture()

    def consume() -> None:
        for attempt in range(60):
            request = Request(
                base_url + "/api/agents/chat",
                data=json.dumps(payload, separators=(",", ":")).encode(),
                method="POST",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "text/event-stream",
                    "Content-Type": "application/json",
                    "User-Agent": BROWSER_USER_AGENT,
                    "X-LibreChat-Generation-Protocol": "2",
                    **({"X-Forwarded-For": FORWARDED_FOR} if FORWARDED_FOR else {}),
                },
            )
            try:
                with urlopen(request, timeout=300) as response:
                    capture.status_code = response.status
                    capture.ready.set()
                    for raw_line in response:
                        line = raw_line.decode(errors="replace").strip()
                        if not line:
                            continue
                        value = line[5:].strip() if line.startswith("data:") else line
                        if not value or value == "[DONE]":
                            continue
                        try:
                            event = json.loads(value)
                            capture.events.append(event)
                            candidates = find_key_strings(event, {"conversationId", "streamId"})
                            for candidate in candidates:
                                try:
                                    uuid.UUID(candidate)
                                except (ValueError, TypeError):
                                    continue
                                capture.conversation_id = candidate
                                capture.conversation_ready.set()
                                break
                        except json.JSONDecodeError:
                            capture.events.append(value)
                    break
            except HTTPError as exc:
                body = exc.read().decode(errors="replace")[:800]
                if exc.code == 503 and "SERVER_NOT_READY" in body and attempt < 59:
                    time.sleep(1)
                    continue
                capture.status_code = exc.code
                capture.error = body
                capture.ready.set()
                break
            except Exception as exc:  # thread transports one concise failure to the caller
                capture.error = str(exc)
                capture.ready.set()
                break
        capture.done.set()

    thread = threading.Thread(target=consume, name=f"librechat-{text}", daemon=True)
    thread.start()
    if not capture.ready.wait(timeout=90):
        raise GateFailure(f"chat start timed out before response headers for {text!r}")
    if capture.status_code not in (200, 201):
        raise GateFailure(
            f"chat start failed for {text!r}: HTTP {capture.status_code}: {capture.error or 'unknown'}"
        )
    if not capture.conversation_ready.wait(timeout=30):
        raise GateFailure(
            f"chat start omitted conversation id for {text!r}; "
            f"event_shapes={event_shapes(capture.events)}"
        )
    return capture.conversation_id, capture, thread


def flatten_strings(value: Any) -> list[str]:
    found: list[str] = []
    if isinstance(value, str):
        found.append(value)
    elif isinstance(value, list):
        for item in value:
            found.extend(flatten_strings(item))
    elif isinstance(value, dict):
        for item in value.values():
            found.extend(flatten_strings(item))
    return found


def find_executor_calls(value: Any) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []
    if isinstance(value, dict):
        name = value.get("name")
        if isinstance(name, str) and name.startswith(EXECUTOR_PREFIX):
            calls.append(value)
        for item in value.values():
            calls.extend(find_executor_calls(item))
    elif isinstance(value, list):
        for item in value:
            calls.extend(find_executor_calls(item))
    return calls


def has_persisted_terminal_message(value: Any) -> bool:
    if not isinstance(value, list):
        return False
    for message in value:
        if not isinstance(message, dict) or message.get("isCreatedByUser") is True:
            continue
        if message.get("unfinished") is True:
            continue
        if flatten_strings(message.get("text")) or flatten_strings(message.get("content")):
            return True
    return False


def safe_excerpt(value: Any, limit: int = 1200) -> str:
    text = " ".join(flatten_strings(value))
    text = re.sub(r"arn:aws[^\s\"']+", "ARN_REDACTED", text)
    text = re.sub(r"\b\d{12}\b", "ACCOUNT_REDACTED", text)
    text = re.sub(r"\b[0-9a-f]{20,}\b", "ID_REDACTED", text, flags=re.I)
    text = re.sub(
        r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
        "UUID_REDACTED",
        text,
        flags=re.I,
    )
    return " ".join(text.split())[-limit:]


def has_noncompliant_finding(text: str) -> bool:
    return "NON_COMPLIANT" in text or "NON-COMPLIANT" in text


def wait_for_status(
    base_url: str,
    token: str,
    conversation_id: str,
    deadline: float,
    wanted: str | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    snapshots: list[dict[str, Any]] = []
    last: dict[str, Any] = {}
    while time.monotonic() < deadline:
        code, value = request_json(
            base_url,
            token,
            "GET",
            f"/api/agents/chat/status/{quote(conversation_id)}",
            timeout=20,
        )
        if code != 200 or not isinstance(value, dict):
            raise GateFailure("chat status did not return a JSON object")
        last = value
        snapshots.append(value)
        if wanted is not None and value.get("status") == wanted:
            return value, snapshots
        # A start response can arrive just before GenerationJobManager publishes
        # the job. Ignore that transient jobless `{active:false}` snapshot; it is
        # not evidence that this conversation completed.
        if wanted is None and value.get("active") is False and value.get("status"):
            return value, snapshots
        if wanted is None and value.get("active") is False and value.get("status") is None:
            try:
                _, history = request_json(
                    base_url,
                    token,
                    "GET",
                    f"/api/messages/{quote(conversation_id)}",
                    timeout=20,
                )
            except GateFailure:
                history = None
            if has_persisted_terminal_message(history):
                return {**value, "status": "settled"}, snapshots
        elif wanted is not None and value.get("active") is False and value.get("status") is None:
            try:
                _, history = request_json(
                    base_url,
                    token,
                    "GET",
                    f"/api/messages/{quote(conversation_id)}",
                    timeout=20,
                )
            except GateFailure:
                history = None
            if has_persisted_terminal_message(history):
                raise GateFailure(
                    f"conversation settled before {wanted}; sanitized_tail={safe_excerpt(history)}"
                )
        time.sleep(1)
    raise GateFailure(f"conversation did not reach {wanted or 'terminal'} state; last={last.get('status')}")


def get_messages(base_url: str, token: str, conversation_id: str) -> Any:
    code, value = request_json(
        base_url,
        token,
        "GET",
        f"/api/messages/{quote(conversation_id)}",
        timeout=30,
    )
    if code != 200:
        raise GateFailure("message readback failed")
    return value


def cleanup_conversation(base_url: str, token: str, conversation_id: str) -> None:
    request_json(
        base_url,
        token,
        "DELETE",
        "/api/convos",
        {"arg": {"conversationId": conversation_id}},
        timeout=30,
    )


def require(condition: bool, message: str) -> None:
    if not condition:
        raise GateFailure(message)


def run() -> int:
    token = env("LIBRECHAT_E2E_BEARER_TOKEN")
    base_url = env("LIBRECHAT_BASE_URL", "http://127.0.0.1:3333").rstrip("/")
    agent_id = env("LIBRECHAT_AGENT_ID", AGENT_ID)
    timeout = float(env("LIBRECHAT_E2E_TIMEOUT", "240"))
    user_id = decode_user_id(token)
    conversations: list[str] = []
    results: list[tuple[str, str]] = []
    initial_status_text = ""
    scenario_name = env("LIBRECHAT_E2E_CONTROL", "s3").lower()
    scenario = SCENARIOS.get(scenario_name)
    if scenario is None:
        raise GateFailure("LIBRECHAT_E2E_CONTROL must be s3 or ssh")
    command = scenario["command"]
    control = scenario["control"]
    label = scenario["label"]

    try:
        # E2E-1: real start + status polling + persisted final response.
        conversation_id, capture, _ = start_chat(base_url, token, user_id, agent_id, "Status")
        conversations.append(conversation_id)
        terminal, snapshots = wait_for_status(
            base_url, token, conversation_id, time.monotonic() + timeout
        )
        capture.done.wait(timeout=10)
        history = get_messages(base_url, token, conversation_id)
        initial_status_text = "\n".join(flatten_strings([snapshots, capture.events, history]))
        require(terminal.get("active") is False, "Status conversation did not complete")
        require(
            not any(snapshot.get("pendingAction") for snapshot in snapshots),
            "Status unexpectedly requested human action",
        )
        require(
            "ui://compliance-agent-v1/fleet-status" in initial_status_text,
            "Status did not contain the fleet rich-result path",
        )
        require(
            scenario["status_marker"] in initial_status_text,
            f"Status did not contain the {label} control marker; "
            f"sanitized_tail={safe_excerpt([snapshots, capture.events, history])}",
        )
        if scenario_name == "s3":
            require(
                "Fix S3" in initial_status_text,
                "Status did not present Fix S3 as next action; "
                f"sanitized_tail={safe_excerpt([snapshots, capture.events, history])}",
            )
        require(
            not find_executor_calls([snapshots, capture.events, history]),
            "Status invoked a remediation executor",
        )
        results.append((f"E2E-1 Status ({label})", "PASS"))

        # E2E-2: fresh exact fix request pauses once at the native approval action.
        fix_id, fix_capture, _ = start_chat(base_url, token, user_id, agent_id, command)
        conversations.append(fix_id)
        pending, fix_snapshots = wait_for_status(
            base_url,
            token,
            fix_id,
            time.monotonic() + timeout,
            wanted="requires_action",
        )
        fix_capture.done.wait(timeout=10)
        action = pending.get("pendingAction")
        require(isinstance(action, dict), "requires_action omitted pendingAction")
        payload = action.get("payload")
        require(isinstance(payload, dict), "pendingAction omitted payload")
        require(payload.get("type") == "tool_approval", "pending action is not tool_approval")
        requests = payload.get("action_requests")
        require(isinstance(requests, list) and len(requests) == 1, "expected exactly one paused call")
        paused = requests[0]
        require(
            isinstance(paused, dict)
            and isinstance(paused.get("name"), str)
            and paused["name"].startswith(EXECUTOR_PREFIX),
            "paused call is not the multi-account executor",
        )
        args = paused.get("arguments")
        if isinstance(args, str):
            args = json.loads(args)
        require(isinstance(args, dict), "paused executor arguments are not an object")
        require(args.get("control") == control, "paused executor has the wrong control")
        require(bool(re.fullmatch(r"[a-f0-9]{20}", str(args.get("batch_id", "")))), "bad batch id")
        require(
            bool(re.fullmatch(r"[a-f0-9]{24}", str(args.get("scope_hash", "")))),
            "bad scope hash",
        )
        action_id = action.get("actionId") or action.get("action_id")
        tool_call_id = paused.get("tool_call_id")
        require(isinstance(action_id, str) and action_id, "pending action omitted action id")
        require(isinstance(tool_call_id, str) and tool_call_id, "paused call omitted tool call id")
        visible_before_ask = "\n".join(flatten_strings([fix_snapshots, fix_capture.events]))
        require(
            CONFIRMATION_RE.search(visible_before_ask) is None,
            "assistant emitted a typed yes/go/approve confirmation prompt",
        )
        unique_executor_ids = {
            call.get("tool_call_id") or call.get("id")
            for call in find_executor_calls([fix_snapshots, fix_capture.events])
        }
        unique_executor_ids.discard(None)
        require(len(unique_executor_ids) == 1, "duplicate executor retry appeared before approval")
        results.append((f"E2E-2 {command} native ASK", "PASS"))

        # E2E-3: the exact API payload that drives ToolApproval is user-facing.
        description = paused.get("description")
        require(isinstance(description, str), "approval description is missing")
        require(
            description.startswith(scenario["approval_prefix"]),
            f"approval description is not the required user-facing {label} prompt",
        )
        require("Selected accounts:" in description and "Change:" in description, "scope/action missing")
        require("ASK - Review execute_multi_account_remediation" not in description, "internal ASK wording leaked")
        review_configs = payload.get("review_configs")
        require(isinstance(review_configs, list) and len(review_configs) == 1, "review config missing")
        require(
            review_configs[0].get("allowed_decisions") == ["approve", "reject"],
            "approval decisions are not restricted to approve/reject",
        )
        results.append((f"E2E-3 Approval UX ({label})", "PASS"))

        # E2E-4: reject through the real resume API; never automate Approve.
        generation_created_at = pending.get("createdAt")
        require(isinstance(generation_created_at, int), "status omitted generationCreatedAt")
        code, resumed = request_json(
            base_url,
            token,
            "POST",
            "/api/agents/chat/resume",
            {
                "conversationId": fix_id,
                "generationCreatedAt": generation_created_at,
                "endpoint": "agents",
                "agent_id": agent_id,
                "model": agent_id,
                "actionId": action_id,
                "decisions": [
                    {
                        "tool_call_id": tool_call_id,
                        "decision": "reject",
                        "reason": f"Automated Issue #162 {label} zero-write rejection proof",
                    }
                ],
            },
            timeout=30,
        )
        require(code in (200, 201), "reject resume did not succeed")
        require(isinstance(resumed, dict) and resumed.get("status") == "resuming", "bad resume ACK")
        rejected_terminal, rejected_snapshots = wait_for_status(
            base_url, token, fix_id, time.monotonic() + timeout
        )
        require(rejected_terminal.get("active") is False, "rejected conversation did not settle")
        rejected_history = get_messages(base_url, token, fix_id)
        rejected_text = "\n".join(flatten_strings([rejected_snapshots, rejected_history]))
        require("AWS change applied" not in rejected_text, "reject path claimed an AWS change")
        rejected_executor_ids = {
            call.get("tool_call_id") or call.get("id")
            for call in find_executor_calls([fix_snapshots, rejected_snapshots, rejected_history])
        }
        rejected_executor_ids.discard(None)
        require(len(rejected_executor_ids) == 1, "reject path produced an executor retry")

        after_id, after_capture, _ = start_chat(base_url, token, user_id, agent_id, "Status")
        conversations.append(after_id)
        after_terminal, after_snapshots = wait_for_status(
            base_url, token, after_id, time.monotonic() + timeout
        )
        after_capture.done.wait(timeout=10)
        after_history = get_messages(base_url, token, after_id)
        after_text = "\n".join(flatten_strings([after_snapshots, after_capture.events, after_history]))
        require(after_terminal.get("active") is False, "post-reject Status did not complete")
        require(
            scenario["status_marker"] in initial_status_text and has_noncompliant_finding(initial_status_text),
            f"initial Status had no {label} finding",
        )
        require(
            scenario["status_marker"] in after_text and has_noncompliant_finding(after_text),
            f"post-reject Status lost the pre-existing {label} finding",
        )
        if scenario_name == "s3":
            require("Fix S3" in after_text, "post-reject Status no longer offered the S3 finding path")
        require("AWS change applied" not in after_text, "post-reject Status claimed an AWS change")
        results.append((f"E2E-4 Reject zero-write ({label})", "PASS"))
    except Exception as exc:
        failed_index = len(results) + 1
        results.append((f"E2E-{failed_index}", f"FAIL — {exc}"))
    finally:
        cleanup_errors: list[str] = []
        for conversation_id in reversed(conversations):
            try:
                cleanup_conversation(base_url, token, conversation_id)
            except Exception as exc:
                cleanup_errors.append(str(exc))
        if cleanup_errors:
            results.append(("CLEANUP", "FAIL — " + "; ".join(cleanup_errors)))

    for name, result in results:
        print(f"{name}: {result}")
    passed = len(results) == 4 and all(result == "PASS" for _, result in results)
    print(f"SUMMARY: {'PASS' if passed else 'FAIL'} ({sum(r == 'PASS' for _, r in results)}/4)")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(run())
