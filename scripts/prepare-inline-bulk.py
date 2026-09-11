#!/usr/bin/env python3
"""Stage exact EC2 worker payload, no credentials and no automatic service start.

Run reviewed output via SSM. Stop the old writer/bridge before starting the new
systemd unit; its separate journal must not overwrite the old demo history.
"""
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
import tarfile

p = argparse.ArgumentParser()
p.add_argument('--manifest', type=Path, required=True)
p.add_argument('--gateway-state', type=Path, required=True)
p.add_argument('--commands-file', type=Path, required=True)
p.add_argument('--update-code-only', action='store_true')
a = p.parse_args()
root = Path(__file__).resolve().parents[1]
buffer = io.BytesIO()
with tarfile.open(fileobj=buffer, mode='w:gz') as tar:
    for path in sorted((root/'pilot_v1').rglob('*')):
        if path.is_file() and path.suffix in {'.py','.html'}:
            tar.add(path, arcname=str(path.relative_to(root)))
    for name in ['integration/bulk-approval-hook.cjs','integration/install-bulk-executor.cjs',
                 'scripts/bulk-demo.py','scripts/provision-bulk-gateway.py','scripts/probe-bulk-policy.py',
                 'scripts/validate-bulk-runtime.py','scripts/bulk-host-demo.sh','requirements-bulk.txt']:
        tar.add(root/name, arcname=name)
payload = buffer.getvalue()
unit = '''[Unit]
Description=AWS SecOps exact governed bulk worker
After=network-online.target
Wants=network-online.target
[Service]
User=ssm-user
WorkingDirectory=/opt/aws-secops-bulk
Environment=HOME=/home/ssm-user
Environment=AWS_PROFILE=vagent
Environment=AWS_REGION=ap-southeast-1
Environment=AWS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
Environment=AWS_MAX_ATTEMPTS=1
ExecStart=/opt/aws-secops-bulk/.venv/bin/python -m pilot_v1.bulk_server --manifest /var/lib/aws-secops-bulk/manifest.json --gateway-state /var/lib/aws-secops-bulk/gateway.json --state /var/lib/aws-secops-bulk/batch.json --port 4444
Restart=on-failure
RestartSec=5
TimeoutStopSec=80
UMask=0077
[Install]
WantedBy=multi-user.target
'''
def stage(path, data, mode='600'):
    encoded = base64.b64encode(data).decode()
    return [f"printf '%s' '{encoded}' | base64 -d > {path}", f'chmod {mode} {path}']
commands = ['#!/bin/sh','set -eu','umask 077','test -d /opt/LibreChat','test -d /opt/aws-secops/.runtime',
            'getent passwd ssm-user >/dev/null',
            'install -d -m 755 /opt/aws-secops-bulk',
            'install -d -m 700 -o ssm-user -g ssm-user /var/lib/aws-secops-bulk']
if not a.update_code_only:
    commands += ['test ! -f /var/lib/aws-secops-bulk/batch.json']
commands += stage('/opt/aws-secops/.runtime/inline-bulk.tgz',payload)
commands += [f"echo '{hashlib.sha256(payload).hexdigest()}  /opt/aws-secops/.runtime/inline-bulk.tgz' | sha256sum -c - >/dev/null",
             'tar -xzf /opt/aws-secops/.runtime/inline-bulk.tgz -C /opt/aws-secops-bulk',
             'test -x /opt/aws-secops-bulk/.venv/bin/python || python3 -m venv /opt/aws-secops-bulk/.venv',
             '/opt/aws-secops-bulk/.venv/bin/pip install --disable-pip-version-check -r /opt/aws-secops-bulk/requirements-bulk.txt',
             'chmod -R a+rX /opt/aws-secops-bulk/pilot_v1 /opt/aws-secops-bulk/integration /opt/aws-secops-bulk/scripts /opt/aws-secops-bulk/.venv']
if not a.update_code_only:
    commands += stage('/var/lib/aws-secops-bulk/manifest.json',a.manifest.read_bytes())
    commands += stage('/var/lib/aws-secops-bulk/gateway.json',a.gateway_state.read_bytes())
    commands += ['chown ssm-user:ssm-user /var/lib/aws-secops-bulk/*.json']
commands += stage('/etc/systemd/system/aws-secops-bulk.service',unit.encode(),'644')
commands += ['install -m 644 /opt/aws-secops-bulk/pilot_v1/mcp_executor.py /opt/aws-secops/pilot_v1/mcp_executor.py',
             'install -m 644 /opt/aws-secops-bulk/pilot_v1/mcp_bridge.py /opt/aws-secops/pilot_v1/mcp_bridge.py',
             'install -m 644 /opt/aws-secops-bulk/integration/bulk-approval-hook.cjs /opt/aws-secops/integration/bulk-approval-hook.cjs',
             'install -m 644 /opt/aws-secops-bulk/integration/install-bulk-executor.cjs /opt/aws-secops/integration/install-bulk-executor.cjs',
             'systemctl daemon-reload',
             'echo INLINE_WORKER_STAGED_NOT_STARTED']
a.commands_file.parent.mkdir(parents=True, exist_ok=True)
a.commands_file.write_text('\n'.join(commands)+'\n'); a.commands_file.chmod(0o600)
print('Private SSM payload prepared; no AWS operation performed')
