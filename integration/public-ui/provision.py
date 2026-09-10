#!/usr/bin/env python3
"""Retained-host HTTPS edge. Inputs are private deployment names, not model data.

Run as root with phase prepare, handoff, tls or rollback. No AWS discovery or
DNS mutation here. Backends and stores are preserved; legacy DNS is untouched.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path('/opt/aws-secops')
PRIVATE = ROOT / '.runtime'
SITE = Path('/etc/nginx/sites-available/aws-secops')
UNIT = Path('/etc/systemd/system/aws-secops-librechat.service')


def run(*args, **kwargs):
    return subprocess.run(args, check=True, text=True, **kwargs)


def nginx(chat, ops, legacy, tls=False):
    proxy = '''proxy_pass http://127.0.0.1:3333;
      proxy_http_version 1.1;
      proxy_set_header Host $host;
      proxy_set_header X-Forwarded-Proto $scheme;
      proxy_set_header X-Forwarded-For $remote_addr;
      proxy_set_header Upgrade $http_upgrade;
      proxy_set_header Connection $secops_connection;
      proxy_buffering off;
      proxy_read_timeout 180s;'''
    result = '''map $http_upgrade $secops_connection { default upgrade; '' close; }
server { listen 80 default_server; server_name _;
  client_max_body_size 20m;
  location / { ''' + proxy + ''' }
}
'''
    # The legacy name and localhost forwards keep exactly their old HTTP route.
    result += f'''server {{ listen 80; server_name {chat} {ops};
  return 308 https://$host$request_uri;
}}
'''
    if not tls:
        return result
    cert = '''ssl_certificate /etc/letsencrypt/live/aws-secops-ui/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/aws-secops-ui/privkey.pem;
  ssl_protocols TLSv1.2 TLSv1.3;'''
    result += f'''server {{ listen 443 ssl; server_name {chat};
  {cert}
  client_max_body_size 20m;
  location / {{ {proxy} }}
}}
map "$request_method:$http_origin" $secops_write_ok {{
  default 0;
  ~^(GET|HEAD|OPTIONS): 1;
  "POST:https://{ops}" 1;
}}
server {{ listen 443 ssl; server_name {ops};
  {cert}
  auth_basic "AWS SecOps Operator";
  auth_basic_user_file /etc/nginx/secops-operator.htpasswd;
  client_max_body_size 256k;
  add_header X-Frame-Options DENY always;
  add_header Content-Security-Policy "frame-ancestors 'none'" always;
  add_header X-Content-Type-Options nosniff always;
  add_header Cache-Control no-store always;
  location / {{
    if ($secops_write_ok = 0) {{ return 403; }}
    proxy_pass http://127.0.0.1:3340;
    proxy_set_header Host localhost:3340;
    proxy_set_header Origin http://localhost:3340;
    proxy_set_header Authorization "";
    proxy_set_header X-Forwarded-For $remote_addr;
    proxy_buffering off;
    proxy_read_timeout 180s;
  }}
}}
'''
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument('phase', choices=['prepare', 'handoff', 'tls', 'rollback'])
    p.add_argument('--config', type=Path, required=True)
    a = p.parse_args()
    os.umask(0o077)
    c = json.loads(a.config.read_text())
    for field in ['chat', 'ops', 'legacy']:
        if not re.fullmatch(r'[a-z0-9]+(?:[.-][a-z0-9]+)+', c[field]):
            raise ValueError('invalid deployment hostname')
    if len({c['chat'], c['ops'], c['legacy']}) != 3:
        raise ValueError('hostnames must differ')
    PRIVATE.mkdir(exist_ok=True, mode=0o700)
    if a.phase == 'prepare':
        if SITE.exists() or UNIT.exists():
            raise RuntimeError('edge already prepared; inspect instead of overwriting')
        if Path('/etc/nginx/sites-enabled').exists():
            raise RuntimeError('existing nginx requires separate adoption review')
        run('systemctl', 'mask', 'nginx.service')
        with (PRIVATE / 'edge-install.log').open('w') as log:
            run('apt-get', 'update', '-qq', stdout=log, stderr=log)
            run('apt-get', 'install', '-y', 'nginx', 'certbot', 'python3-certbot-dns-route53',
                stdout=log, stderr=log, env={**os.environ, 'DEBIAN_FRONTEND': 'noninteractive'})
        default = Path('/etc/nginx/sites-enabled/default')
        if default.is_symlink():
            default.rename('/etc/nginx/sites-available/default.disabled-link')
        SITE.write_text(nginx(c['chat'], c['ops'], c['legacy']))
        Path('/etc/nginx/sites-enabled/aws-secops').symlink_to(SITE)
        UNIT.write_text('''[Unit]
Description=Retained LibreChat behind AWS SecOps edge
After=network-online.target
[Service]
WorkingDirectory=/opt/LibreChat
Environment=HOST=127.0.0.1
Environment=PORT=3333
Environment=NODE_ENV=production
ExecStart=/usr/bin/node api/server/index.js
Restart=on-failure
RestartSec=5
UMask=0077
[Install]
WantedBy=multi-user.target
''')
        run('nginx', '-t')
        print('EDGE_PREPARED; existing LibreChat still running on port 80')
    elif a.phase == 'handoff':
        if run('ss', '-ltnH', 'sport = :3333', capture_output=True).stdout.strip():
            raise RuntimeError('3333 occupied; refusing handoff')
        line = run('ss', '-ltnp', 'sport = :80', capture_output=True).stdout
        match = re.search(r'pid=(\d+)', line)
        if not match:
            raise RuntimeError('legacy listener absent')
        pid = match[1]
        if Path('/proc/' + pid + '/cwd').resolve() != Path('/opt/LibreChat'):
            raise RuntimeError('legacy listener owner differs')
        if b'api/server/index.js' not in Path('/proc/' + pid + '/cmdline').read_bytes():
            raise RuntimeError('legacy command differs')
        run('kill', '-TERM', pid)
        run('systemctl', 'daemon-reload')
        run('systemctl', 'enable', '--now', 'aws-secops-librechat.service')
        run('curl', '--retry', '15', '--retry-connrefused', '--retry-delay', '1',
            '--max-time', '5', '-fsS', '-o', '/dev/null', 'http://localhost:3333/api/config')
        run('systemctl', 'unmask', 'nginx.service')
        run('systemctl', 'enable', '--now', 'nginx.service')
        run('curl', '-fsS', '-o', '/dev/null', '-H', 'Host: ' + c['legacy'], 'http://localhost/api/config')
        print('LEGACY_HANDOFF=PASS')
    elif a.phase == 'tls':
        if not Path('/etc/nginx/secops-operator.htpasswd').is_file():
            raise RuntimeError('operator password hash file missing')
        run('certbot', 'certonly', '--dns-route53', '--non-interactive', '--agree-tos',
            '--register-unsafely-without-email', '--cert-name', 'aws-secops-ui',
            '-d', c['chat'], '-d', c['ops'])
        before = SITE.read_text()
        SITE.write_text(nginx(c['chat'], c['ops'], c['legacy'], tls=True))
        try:
            run('nginx', '-t')
        except Exception:
            SITE.write_text(before)
            raise
        run('systemctl', 'reload', 'nginx')
        hook = Path('/etc/letsencrypt/renewal-hooks/deploy/secops-nginx')
        hook.write_text('#!/bin/sh\n/usr/sbin/nginx -t && /bin/systemctl reload nginx\n')
        hook.chmod(0o700)
        run('systemctl', 'enable', '--now', 'certbot.timer')
        print('HTTPS_EDGE=READY')
    else:
        # Leaves certificates, accounts, stores and DNS intact. Closes the new edge.
        run('systemctl', 'stop', 'nginx', 'aws-secops-librechat')
        run('systemctl', 'disable', 'nginx', 'aws-secops-librechat')
        with (PRIVATE / 'legacy-rollback.log').open('a') as log:
            subprocess.Popen(['/usr/bin/node', 'api/server/index.js'], cwd='/opt/LibreChat',
                env={**os.environ, 'HOST': '0.0.0.0', 'PORT': '80', 'NODE_ENV': 'production'},
                stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True)
        print('LEGACY_ROLLBACK_STARTED; verify port 80 before claiming recovery')


if __name__ == '__main__':
    main()
