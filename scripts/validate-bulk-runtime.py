#!/usr/bin/env python3
"""Bounded API durability proof on the owned EC2 worker; not a native-UI claim.

Default reads status only. --interrupt explicitly exercises the approved
ten-bucket validation, process interruption, reconciliation and continuation.
"""
import argparse
import json
from pathlib import Path
import subprocess
import time
from urllib.request import Request, urlopen

BASE = 'http://localhost:4444'


def api(path, data=None):
    request = Request(BASE+path, data=None if data is None else json.dumps(data).encode(),
                      headers={'Content-Type':'application/json','Origin':BASE})
    with urlopen(request, timeout=60) as response:
        return json.load(response)


def summary():
    return api('/api/v1/list_batches')['items'][0]


def wait(predicate, seconds=300):
    deadline = time.monotonic()+seconds
    while time.monotonic() < deadline:
        try:
            value = summary()
        except OSError:
            time.sleep(1); continue
        if predicate(value): return value
        time.sleep(1)
    raise RuntimeError('bounded progress timeout; no automatic write retry')


def main():
    p = argparse.ArgumentParser()
    mode = p.add_mutually_exclusive_group()
    mode.add_argument('--interrupt',action='store_true')
    mode.add_argument('--execute',type=int,choices=(10,50,100),help='explicitly approve the exact prepared validation fleet')
    p.add_argument('--output',type=Path)
    a = p.parse_args(); initial = summary()
    if not a.interrupt and not a.execute:
        print(json.dumps({k:initial[k] for k in ('total','decision','counts','verified','execution_active')})); return
    expected = a.execute or 10
    if initial['total'] != expected or initial['context']['mode'] != 'LIVE' or initial['context']['profile'] != 'vagent' or initial['decision'] != 'PENDING':
        raise RuntimeError('requires the exact prepared vagent validation batch')
    user = subprocess.check_output(['systemctl','show','aws-secops-bulk.service','-p','User','--value'],text=True).strip()
    if user != 'ssm-user': raise RuntimeError('unexpected worker identity')
    started = time.monotonic()
    args = {'batch_id':initial['batch_id'],'approval_hash':initial['approval_hash']}
    api('/api/bulk/start',args)
    if a.execute:
        final = wait(lambda b: not b['execution_active'] and not b['counts'].get('APPROVED'),300)
        record = dict(initial=initial,final=final,elapsed_seconds=round(time.monotonic()-started,3),proof='API/runtime only; no browser assertion')
        if a.output:
            a.output.write_text(json.dumps(record)); a.output.chmod(0o600)
        if final['verified'] != expected or final['counts'] != {'COMPLETED':expected}:
            raise RuntimeError('scale result incomplete; inspect saved result, no automatic retry')
        print(json.dumps({'scale':expected,'result':'PASS','elapsed_seconds':record['elapsed_seconds'],'counts':final['counts'],'usage':final['usage']}))
        return
    running = wait(lambda b: b['counts'].get('RUNNING',0)>0,30)
    subprocess.run(['systemctl','kill','--kill-who=main','--signal=SIGKILL','aws-secops-bulk.service'],check=True)
    restarted = wait(lambda b: b['counts'].get('UNKNOWN',0)>0,60)
    if restarted['execution_active']: raise RuntimeError('restart must not auto-resume')
    reconciled = api('/api/bulk/reconcile',{'batch_id':initial['batch_id']})
    if reconciled['counts'].get('UNKNOWN'): raise RuntimeError('provider reconciliation unavailable; stop')
    if reconciled['counts'].get('APPROVED'):
        api('/api/bulk/start',args)  # explicit continuation within the same approved scope
    terminal = wait(lambda b: not b['execution_active'] and not b['counts'].get('APPROVED'),300)
    if terminal['counts'].get('UNKNOWN'): raise RuntimeError('ambiguous continuation; stop')
    # Failed reconciled items are never replayed. A fresh provider preview and
    # separate approval can address remaining noncompliance; completed ones skip.
    fresh = api('/api/bulk/new-preview',{})
    api('/api/bulk/start',{'batch_id':fresh['batch_id'],'approval_hash':fresh['approval_hash']})
    final = wait(lambda b: not b['execution_active'] and b['verified']==10,300)
    record = dict(initial=initial,running=running,restarted=restarted,reconciled=reconciled,terminal=terminal,final=final,elapsed_seconds=round(time.monotonic()-started,3),proof='API/runtime only; no browser assertion')
    if a.output:
        a.output.write_text(json.dumps(record)); a.output.chmod(0o600)
    print('INTERRUPTION_UNKNOWN_RECONCILIATION_CONTINUATION=PASS VERIFIED=10',flush=True)
    print(json.dumps({'elapsed_seconds':record['elapsed_seconds'],'final_counts':final['counts'],'usage':final['usage']}))


if __name__ == '__main__': main()
