#!/usr/bin/env python3
"""Prepare a one-time private store handoff after the local writer is stopped.

Leaves original files intact. Remote migration refuses an existing store.
The caller verifies listener ownership and dispatches through the shared SSM tool.
"""
import argparse
import base64
import hashlib
import io
import os
from pathlib import Path
import tarfile

parser = argparse.ArgumentParser()
parser.add_argument("--pilot-state", type=Path, required=True)
parser.add_argument("--backlog", type=Path, required=True)
parser.add_argument("--commands-file", type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
files = [(args.pilot_state, ".runtime/pilot-state.json"),
         (args.backlog, ".runtime/backlog.json"),
         (args.backlog.with_suffix(".jobs.json"), ".runtime/backlog.jobs.json"),
         (root / "pilot_v1/runtime_host.py", "pilot_v1/runtime_host.py")]
buffer = io.BytesIO()
with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
    for source, target in files:
        if not source.is_file() or source.is_symlink():
            raise ValueError("expected regular private source file")
        archive.add(source, arcname=target)
encoded = base64.b64encode(buffer.getvalue()).decode()
unit = """[Unit]
Description=AWS SecOps personal-lab backend
After=network-online.target
[Service]
Type=simple
WorkingDirectory=/opt/aws-secops
ExecStart=/opt/aws-secops/.venv-mcp/bin/python -m pilot_v1.runtime_host
UMask=0077
Restart=no
[Install]
WantedBy=multi-user.target
"""
commands = ["#!/bin/sh", "set -eu", "umask 077", "test -d /opt/aws-secops",
            "test ! -e /opt/aws-secops/.runtime/backlog.json",
            "test ! -e /etc/systemd/system/aws-secops-backend.service",
            "test -z \"$(ss -ltnH 'sport = :3340')\"",
            "install -d -m 700 /opt/aws-secops/.runtime",
            ": > /opt/aws-secops/.runtime/handoff.b64"]
commands += ["printf '%s' '" + encoded[i:i + 8000] + "' >> /opt/aws-secops/.runtime/handoff.b64"
             for i in range(0, len(encoded), 8000)]
commands += ["base64 -d /opt/aws-secops/.runtime/handoff.b64 > /opt/aws-secops/.runtime/handoff.tgz",
             "tar -xzf /opt/aws-secops/.runtime/handoff.tgz -C /opt/aws-secops"]
for source, target in files:
    commands.append(f"echo '{hashlib.sha256(source.read_bytes()).hexdigest()}  /opt/aws-secops/{target}' | sha256sum -c - >/dev/null")
commands += ["echo STORE_HANDOFF_HASHES=PASS",
             "printf '%s' '" + base64.b64encode(unit.encode()).decode() + "' | base64 -d > /etc/systemd/system/aws-secops-backend.service",
             "systemctl daemon-reload", "systemctl enable --now aws-secops-backend.service",
             "sleep 5", "systemctl is-active aws-secops-backend.service",
             "curl -fsS --max-time 10 http://localhost:3340/api/v1/get_source_health | /opt/aws-secops/.venv-mcp/bin/python -c 'import json,sys; d=json.load(sys.stdin); print(\"REMOTE_BACKEND=\"+d[\"store\"])'",
             "ps -o user= -p $(ss -ltnp 'sport = :80' | sed -n 's/.*pid=\\([0-9][0-9]*\\).*/\\1/p' | head -n 1)"]
args.commands_file.parent.mkdir(parents=True, exist_ok=True)
with os.fdopen(os.open(args.commands_file, os.O_CREAT | os.O_TRUNC | os.O_WRONLY, 0o600), "w") as stream:
    stream.write("\n".join(commands) + "\n")
print("PRIVATE_STORE_HANDOFF_COMMANDS_READY")
