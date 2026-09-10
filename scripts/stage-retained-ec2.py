#!/usr/bin/env python3
"""Build a private SSM command payload for the existing, identified lab host.

Does not dispatch AWS calls, stop services, move stores or start the backend.
Use the shared SSM runner after reviewing the generated POSIX command file.
"""
import argparse
import base64
import hashlib
import io
import os
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--commands-file", type=Path, required=True)
args = parser.parse_args()
buffer = io.BytesIO()
with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
    for path in sorted((ROOT / "pilot_v1").rglob("*")):
        if path.is_file() and path.suffix in {".py", ".html"}:
            archive.add(path, arcname=str(path.relative_to(ROOT)))
    archive.add(ROOT / "requirements-mcp.txt", arcname="requirements-mcp.txt")
    archive.add(ROOT / "integration/install-reader.cjs", arcname="integration/install-reader.cjs")
payload = buffer.getvalue()
encoded = base64.b64encode(payload).decode()
commands = ["#!/bin/sh", "set -eu", "umask 077",
            "test -d /opt/LibreChat", "install -d -m 700 /opt/aws-secops",
            "test ! -f /opt/aws-secops/.staging.lock", "touch /opt/aws-secops/.staging.lock",
            "trap 'rm -f /opt/aws-secops/.staging.lock' EXIT",
            ": > /opt/aws-secops/source.tgz.b64"]
commands += ["printf '%s' '" + encoded[i:i + 8000] + "' >> /opt/aws-secops/source.tgz.b64"
             for i in range(0, len(encoded), 8000)]
commands += ["base64 -d /opt/aws-secops/source.tgz.b64 > /opt/aws-secops/source.tgz",
             f"echo '{hashlib.sha256(payload).hexdigest()}  /opt/aws-secops/source.tgz' | sha256sum -c - >/dev/null",
             "tar -xzf /opt/aws-secops/source.tgz -C /opt/aws-secops",
             "cd /opt/aws-secops",
             "if ! python3 -m ensurepip --version >/dev/null 2>&1; then apt-get update -qq >/opt/aws-secops/apt-install.log 2>&1; DEBIAN_FRONTEND=noninteractive apt-get install -y python3-venv >>/opt/aws-secops/apt-install.log 2>&1; fi",
             "python3 -m venv .venv-mcp",
             ".venv-mcp/bin/pip -q install -r requirements-mcp.txt",
             "npm install --prefix /opt/aws-secops/cli --no-audit --no-fund @aws/agentcore@0.28.1 >/opt/aws-secops/install.log 2>&1",
             "echo RETAINED_EC2_CODE_STAGE=PASS",
             "echo BACKEND_NOT_STARTED=TRUE"]
args.commands_file.parent.mkdir(parents=True, exist_ok=True)
fd = os.open(args.commands_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
with os.fdopen(fd, "w") as stream:
    stream.write("\n".join(commands) + "\n")
print(f"PRIVATE_STAGE_COMMANDS_READY BYTES={len(payload)}")
