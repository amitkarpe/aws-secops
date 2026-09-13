#!/usr/bin/env python3
"""Operator-only repeat-demo control; uses the same authenticated-local prepare API as the homepage."""
from __future__ import annotations
import argparse,json
from urllib.request import ProxyHandler,Request,build_opener
BASE='http://localhost:4444'
def call(path,payload=None):
    data=None if payload is None else json.dumps(payload).encode();headers={'Origin':BASE,'Content-Type':'application/json'}
    with build_opener(ProxyHandler({})).open(Request(BASE+path,data=data,headers=headers),timeout=180) as r:return json.load(r)
p=argparse.ArgumentParser();sub=p.add_subparsers(dest='cmd',required=True);sub.add_parser('status');r=sub.add_parser('reset');g=r.add_mutually_exclusive_group(required=True);g.add_argument('--s3',action='store_true');g.add_argument('--sg',action='store_true');g.add_argument('--all',action='store_true');r.add_argument('--confirm',action='store_true',help='required acknowledgement of intentional demo noncompliance')
a=p.parse_args()
if a.cmd=='status':print(json.dumps(call('/api/operator/status'),indent=2));raise SystemExit(0)
if not a.confirm:p.error('reset requires --confirm')
families=['s3','sg'] if a.all else ['s3' if a.s3 else 'sg']
for family in families:
    preview=call('/api/operator/prepare-preview',{'family':family});print(preview['warning']);print('RESOURCES='+str(preview['resource_count'])+' ACTION='+preview['action'])
    result=call('/api/operator/prepare',{'family':family,'confirmation_token':preview['confirmation_token']});print(result['message'])
    if result.get('status')!='DEMO_READY':raise SystemExit(2)
