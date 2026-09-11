#!/usr/bin/env python3
"""Prepare one reviewed SSM payload for SG compliance/operator deployment."""
from __future__ import annotations
import argparse,base64,hashlib,io
from pathlib import Path
import tarfile
p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,required=True);p.add_argument('--gateway-state',type=Path,required=True);p.add_argument('--commands-file',type=Path,required=True);p.add_argument('--update-code-only',action='store_true');a=p.parse_args();root=Path(__file__).resolve().parents[1]
buffer=io.BytesIO()
with tarfile.open(fileobj=buffer,mode='w:gz') as tar:
    for path in sorted((root/'pilot_v1').rglob('*')):
        if path.is_file() and path.suffix in {'.py','.json'}:tar.add(path,arcname=str(path.relative_to(root)))
    for name in ['integration/sg-approval-hook.cjs','integration/install-compliance.cjs','integration/compliance-agent.json','scripts/sg-demo.py','scripts/provision-sg-gateway.py','scripts/probe-sg-policy.py','scripts/demo-control.py','requirements-bulk.txt']:tar.add(root/name,arcname=name)
payload=buffer.getvalue()
unit='''[Unit]
Description=AWS SecOps governed Security Group compliance worker
After=network-online.target
Wants=network-online.target
[Service]
User=ssm-user
WorkingDirectory=/opt/aws-secops-sg
Environment=HOME=/home/ssm-user
Environment=AWS_PROFILE=vagent
Environment=AWS_REGION=ap-southeast-1
Environment=AWS_MAX_ATTEMPTS=1
ExecStart=/opt/aws-secops-sg/.venv/bin/python -m pilot_v1.sg_operator_server --manifest /var/lib/aws-secops-sg/manifest.json --gateway-state /var/lib/aws-secops-sg/gateway.json --state /var/lib/aws-secops-sg/batch.json --port 4455
Restart=on-failure
RestartSec=5
TimeoutStopSec=80
UMask=0077
[Install]
WantedBy=multi-user.target
'''
def stage(path,data,mode='600'):
    encoded=base64.b64encode(data).decode();return [f"printf '%s' '{encoded}' | base64 -d > {path}",f'chmod {mode} {path}']
commands=['#!/bin/sh','set -eu','umask 077','test -d /opt/LibreChat','test -d /opt/aws-secops/.runtime','getent passwd ssm-user >/dev/null','install -d -m 755 /opt/aws-secops-sg','install -d -m 700 -o ssm-user -g ssm-user /var/lib/aws-secops-sg']
if not a.update_code_only:commands+=['test ! -f /var/lib/aws-secops-sg/batch.json']
commands+=stage('/opt/aws-secops/.runtime/sg-compliance.tgz',payload)
commands += [f"echo '{hashlib.sha256(payload).hexdigest()}  /opt/aws-secops/.runtime/sg-compliance.tgz' | sha256sum -c - >/dev/null",'tar -xzf /opt/aws-secops/.runtime/sg-compliance.tgz -C /opt/aws-secops-sg','test -x /opt/aws-secops-sg/.venv/bin/python || python3 -m venv /opt/aws-secops-sg/.venv','/opt/aws-secops-sg/.venv/bin/pip install --disable-pip-version-check -r /opt/aws-secops-sg/requirements-bulk.txt','chmod -R a+rX /opt/aws-secops-sg/pilot_v1 /opt/aws-secops-sg/integration /opt/aws-secops-sg/scripts /opt/aws-secops-sg/.venv']
if not a.update_code_only:
    commands+=stage('/var/lib/aws-secops-sg/manifest.json',a.manifest.read_bytes());commands+=stage('/var/lib/aws-secops-sg/gateway.json',a.gateway_state.read_bytes());commands+=['chown ssm-user:ssm-user /var/lib/aws-secops-sg/*.json']
commands+=stage('/etc/systemd/system/aws-secops-sg.service',unit.encode(),'644')
commands += ['install -m 644 /opt/aws-secops-sg/pilot_v1/compliance_mcp.py /opt/aws-secops/pilot_v1/compliance_mcp.py','install -m 644 /opt/aws-secops-sg/pilot_v1/operator_mcp.py /opt/aws-secops/pilot_v1/operator_mcp.py','install -m 644 /opt/aws-secops-sg/integration/sg-approval-hook.cjs /opt/aws-secops/integration/sg-approval-hook.cjs','install -m 644 /opt/aws-secops-sg/integration/install-compliance.cjs /opt/aws-secops/integration/install-compliance.cjs','install -m 644 /opt/aws-secops-sg/integration/compliance-agent.json /opt/aws-secops/integration/compliance-agent.json','systemctl daemon-reload','echo SG_COMPLIANCE_STAGED_NOT_STARTED']
a.commands_file.parent.mkdir(parents=True,exist_ok=True);a.commands_file.write_text('\n'.join(commands)+'\n');a.commands_file.chmod(0o600)
print('Private SSM deployment payload prepared; no AWS operation performed')
