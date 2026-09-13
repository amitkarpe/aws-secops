#!/usr/bin/env python3
"""Stage exact EC2 bulk/operator payload; no automatic service start."""
import argparse
import base64
import hashlib
import io
from pathlib import Path
import tarfile

SSM_SAFE_COMMAND_BYTES = 80_000
UPDATE_FILES = [
    "pilot_v1/control_catalog.py",
    "pilot_v1/demo_prepare.py",
    "pilot_v1/log_proof.py",
    "pilot_v1/operator_mcp.py",
    "pilot_v1/operator_protocol.py",
    "pilot_v1/operator_server.py",
    "pilot_v1/static/operator.html",
    "scripts/demo-control.py",
    "scripts/probe-bulk-policy.py",
]
FULL_EXTRA_FILES = [
    "integration/bulk-approval-hook.cjs",
    "integration/install-bulk-executor.cjs",
    "scripts/bulk-demo.py",
    "scripts/provision-bulk-gateway.py",
    "scripts/probe-bulk-policy.py",
    "scripts/validate-bulk-runtime.py",
    "scripts/bulk-host-demo.sh",
    "scripts/demo-control.py",
    "requirements-bulk.txt",
]

p = argparse.ArgumentParser()
p.add_argument("--manifest", type=Path, required=True)
p.add_argument("--gateway-state", type=Path, required=True)
p.add_argument("--commands-file", type=Path, required=True)
p.add_argument("--update-code-only", action="store_true")
a = p.parse_args()
root = Path(__file__).resolve().parents[1]
buffer = io.BytesIO()
with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
    if a.update_code_only:
        for name in UPDATE_FILES:
            tar.add(root / name, arcname=name)
    else:
        for path in sorted((root / "pilot_v1").rglob("*")):
            if path.is_file() and path.suffix in {".py", ".html"}:
                tar.add(path, arcname=str(path.relative_to(root)))
        for name in FULL_EXTRA_FILES:
            tar.add(root / name, arcname=name)
payload = buffer.getvalue()
unit = """[Unit]
Description=AWS SecOps exact governed bulk worker and operator homepage
After=network-online.target aws-secops-sg.service
Wants=network-online.target
[Service]
User=ssm-user
WorkingDirectory=/opt/aws-secops-bulk
Environment=HOME=/home/ssm-user
Environment=AWS_PROFILE=vagent
Environment=AWS_REGION=ap-southeast-1
Environment=AWS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
Environment=AWS_MAX_ATTEMPTS=1
Environment=SECOPS_SG_BACKEND_URL=http://localhost:4455
ExecStart=/opt/aws-secops-bulk/.venv/bin/python -m pilot_v1.operator_server --manifest /var/lib/aws-secops-bulk/manifest.json --gateway-state /var/lib/aws-secops-bulk/gateway.json --state /var/lib/aws-secops-bulk/batch.json --port 4444
Restart=on-failure
RestartSec=5
TimeoutStopSec=80
UMask=0077
[Install]
WantedBy=multi-user.target
"""


def stage(path: str, data: bytes, mode: str = "600") -> list[str]:
    encoded = base64.b64encode(data).decode()
    return [f"printf '%s' '{encoded}' | base64 -d > {path}", f"chmod {mode} {path}"]


commands = [
    "#!/bin/sh", "set -eu", "umask 077", "test -d /opt/LibreChat", "test -d /opt/aws-secops/.runtime",
    "getent passwd ssm-user >/dev/null", "install -d -m 755 /opt/aws-secops-bulk",
    "install -d -m 700 -o ssm-user -g ssm-user /var/lib/aws-secops-bulk",
]
if a.update_code_only:
    commands += [
        "test -f /var/lib/aws-secops-bulk/manifest.json",
        "test -f /var/lib/aws-secops-bulk/gateway.json",
        "test -f /var/lib/aws-secops-bulk/batch.json",
        "test -f /opt/aws-secops-bulk/pilot_v1/bulk_server.py",
        "test -f /opt/aws-secops-bulk/pilot_v1/mcp_executor.py",
        "test -f /opt/aws-secops-bulk/pilot_v1/mcp_bridge.py",
        "test -f /opt/aws-secops-bulk/integration/bulk-approval-hook.cjs",
        "test -f /opt/aws-secops-bulk/integration/install-bulk-executor.cjs",
        "test -f /opt/aws-secops-bulk/requirements-bulk.txt",
    ]
else:
    commands += ["test ! -f /var/lib/aws-secops-bulk/batch.json"]
commands += stage("/opt/aws-secops/.runtime/inline-bulk.tgz", payload)
commands += [
    f"echo '{hashlib.sha256(payload).hexdigest()}  /opt/aws-secops/.runtime/inline-bulk.tgz' | sha256sum -c - >/dev/null",
    "tar -xzf /opt/aws-secops/.runtime/inline-bulk.tgz -C /opt/aws-secops-bulk",
    "test -x /opt/aws-secops-bulk/.venv/bin/python || python3 -m venv /opt/aws-secops-bulk/.venv",
    "/opt/aws-secops-bulk/.venv/bin/pip install --disable-pip-version-check -r /opt/aws-secops-bulk/requirements-bulk.txt",
    "chmod -R a+rX /opt/aws-secops-bulk/pilot_v1 /opt/aws-secops-bulk/integration /opt/aws-secops-bulk/scripts /opt/aws-secops-bulk/.venv",
]
if not a.update_code_only:
    commands += stage("/var/lib/aws-secops-bulk/manifest.json", a.manifest.read_bytes())
    commands += stage("/var/lib/aws-secops-bulk/gateway.json", a.gateway_state.read_bytes())
    commands += ["chown ssm-user:ssm-user /var/lib/aws-secops-bulk/*.json"]
commands += stage("/etc/systemd/system/aws-secops-bulk.service", unit.encode(), "644")
commands += [
    "install -m 644 /opt/aws-secops-bulk/pilot_v1/mcp_executor.py /opt/aws-secops/pilot_v1/mcp_executor.py",
    "install -m 644 /opt/aws-secops-bulk/pilot_v1/mcp_bridge.py /opt/aws-secops/pilot_v1/mcp_bridge.py",
    "install -m 644 /opt/aws-secops-bulk/pilot_v1/operator_mcp.py /opt/aws-secops/pilot_v1/operator_mcp.py",
    "install -m 644 /opt/aws-secops-bulk/integration/bulk-approval-hook.cjs /opt/aws-secops/integration/bulk-approval-hook.cjs",
    "install -m 644 /opt/aws-secops-bulk/integration/install-bulk-executor.cjs /opt/aws-secops/integration/install-bulk-executor.cjs",
    "systemctl daemon-reload", "echo INLINE_WORKER_STAGED_NOT_STARTED",
]
a.commands_file.parent.mkdir(parents=True, exist_ok=True)
a.commands_file.write_text("\n".join(commands) + "\n")
a.commands_file.chmod(0o600)
command_bytes = a.commands_file.stat().st_size
if a.update_code_only and command_bytes > SSM_SAFE_COMMAND_BYTES:
    a.commands_file.unlink()
    raise RuntimeError(f"update-code-only SSM command payload exceeds safe budget: {command_bytes} bytes")
print(f"Private SSM payload prepared; no AWS operation performed; SSM_COMMAND_BYTES={command_bytes}")
