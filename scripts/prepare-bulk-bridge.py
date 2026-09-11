#!/usr/bin/env python3
"""Prepare reviewed SSM deployment payload; does not dispatch it or copy AWS auth.

Dedicated SSH key is restricted to loopback reverse forwarding; existing keys,
services and stores are preserved. Host fingerprint must be pinned via SSM.
"""
import argparse
import base64
import io
from pathlib import Path
import re
import tarfile
import hashlib

root = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser()
p.add_argument('--public-key', type=Path, required=True)
p.add_argument('--commands-file', type=Path, required=True)
a = p.parse_args()
key = a.public_key.read_text().strip().split()
if len(key) < 2 or key[0] != 'ssh-ed25519' or not re.fullmatch(r'[A-Za-z0-9+/=]+', key[1]):
    raise ValueError('dedicated ed25519 public transport key required')
line = ('restrict,port-forwarding,permitlisten="127.0.0.1:4444",permitopen="127.0.0.1:4444",'
        'command="/bin/false" ' + ' '.join(key[:2]) + ' aws-secops-bulk-bridge')
buffer = io.BytesIO()
with tarfile.open(fileobj=buffer, mode='w:gz') as archive:
    for path in sorted((root / 'pilot_v1').rglob('*')):
        if path.is_file() and path.suffix in {'.py', '.html'}:
            archive.add(path, arcname=str(path.relative_to(root)))
    for name in ['integration/install-reader.cjs', 'integration/public-ui/provision.py',
                 'integration/reader-agent.json', 'integration/bulk-reader-agent.json']:
        archive.add(root / name, arcname=name)
payload = buffer.getvalue()
encoded = base64.b64encode(payload).decode()
commands = ['#!/bin/sh', 'set -eu', 'umask 077',
            'test -d /opt/aws-secops/.runtime', 'test -d /opt/LibreChat',
            'test -x /opt/aws-secops/.venv-mcp/bin/python',
            ': > /opt/aws-secops/.runtime/bulk-code.b64']
commands += ["printf '%s' '"+encoded[i:i+8000]+"' >> /opt/aws-secops/.runtime/bulk-code.b64" for i in range(0,len(encoded),8000)]
commands += ['base64 -d /opt/aws-secops/.runtime/bulk-code.b64 > /opt/aws-secops/.runtime/bulk-code.tgz',
             f"echo '{hashlib.sha256(payload).hexdigest()}  /opt/aws-secops/.runtime/bulk-code.tgz' | sha256sum -c - >/dev/null",
             'test -f /opt/aws-secops/.runtime/before-bulk-code.tgz || tar -czf /opt/aws-secops/.runtime/before-bulk-code.tgz -C /opt/aws-secops pilot_v1 integration',
             'tar -xzf /opt/aws-secops/.runtime/bulk-code.tgz -C /opt/aws-secops',
             'install -d -m 700 -o ubuntu -g ubuntu /home/ubuntu/.ssh',
             'touch /home/ubuntu/.ssh/authorized_keys',
             "if grep -q ' aws-secops-bulk-bridge$' /home/ubuntu/.ssh/authorized_keys; then",
             "  grep -Fx '"+line+"' /home/ubuntu/.ssh/authorized_keys >/dev/null",
             'else', "  printf '\\n%s\\n' '"+line+"' >> /home/ubuntu/.ssh/authorized_keys", 'fi',
             'chown ubuntu:ubuntu /home/ubuntu/.ssh/authorized_keys',
             'chmod 600 /home/ubuntu/.ssh/authorized_keys',
             'systemctl start ssh',
             '/usr/sbin/sshd -T | grep -E "^(allowtcpforwarding|gatewayports) "',
             'echo BULK_CODE_AND_RESTRICTED_TRANSPORT_KEY=STAGED',
             'echo NO_READER_OR_EDGE_RESTART_YET']
a.commands_file.parent.mkdir(parents=True, exist_ok=True)
with a.commands_file.open('w') as f:
    f.write('\n'.join(commands)+'\n')
a.commands_file.chmod(0o600)
print('Private reviewed payload prepared; no AWS operation performed')
