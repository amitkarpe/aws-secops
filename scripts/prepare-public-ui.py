#!/usr/bin/env python3
"""Prepare private SSM payload; never emit operator passwords or resource IDs."""
import argparse
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import secrets
import subprocess
import tarfile

p = argparse.ArgumentParser()
p.add_argument('--chat', required=True)
p.add_argument('--ops', required=True)
p.add_argument('--legacy', required=True)
p.add_argument('--private-dir', type=Path, required=True)
a = p.parse_args()
os.umask(0o077)
a.private_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
root = Path(__file__).resolve().parents[1]
login_file = a.private_dir / 'operator-login.json'
if login_file.exists():
    raise SystemExit('Existing operator credential; do not rotate implicitly')
password = secrets.token_urlsafe(32)
login_file.write_text(json.dumps({'username': 'amit', 'password': password, 'url': 'https://' + a.ops}))
password_hash = subprocess.run(['openssl', 'passwd', '-6', '-stdin'], input=password,
                               capture_output=True, text=True, check=True).stdout.strip()
config = json.dumps({'chat': a.chat, 'ops': a.ops, 'legacy': a.legacy})
data = io.BytesIO()
with tarfile.open(fileobj=data, mode='w:gz') as tar:
    for source in ['integration/public-ui/provision.py', 'pilot_v1/mcp_bridge.py']:
        tar.add(root / source, arcname=source)
    for name, content in [('.runtime/edge.json', config),
                          ('.runtime/operator.htpasswd', 'amit:' + password_hash + '\n')]:
        info = tarfile.TarInfo(name); info.size = len(content.encode()); info.mode = 0o600
        tar.addfile(info, io.BytesIO(content.encode()))
encoded = base64.b64encode(data.getvalue()).decode()
commands = ['#!/bin/sh', 'set -eu', 'umask 077', 'cd /opt/aws-secops',
            'test ! -f .runtime/edge.json', ': > .runtime/edge-stage.b64']
commands += ["printf '%s' '" + encoded[i:i+8000] + "' >> .runtime/edge-stage.b64" for i in range(0,len(encoded),8000)]
commands += ['base64 -d .runtime/edge-stage.b64 > .runtime/edge-stage.tgz',
             "echo '"+hashlib.sha256(data.getvalue()).hexdigest()+"  .runtime/edge-stage.tgz' | sha256sum -c - >/dev/null",
             'tar -xzf .runtime/edge-stage.tgz',
             'python3 integration/public-ui/provision.py prepare --config .runtime/edge.json',
             'install -o root -g www-data -m 640 .runtime/operator.htpasswd /etc/nginx/secops-operator.htpasswd',
             'echo EDGE_STAGE=PASS']
(a.private_dir / 'prepare.commands').write_text('\n'.join(commands)+'\n')
print('PRIVATE_EDGE_PAYLOAD_READY; operator credential stored privately, not printed')
